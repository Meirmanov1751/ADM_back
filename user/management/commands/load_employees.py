import base64
import json
import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.db.utils import IntegrityError, OperationalError
from user.models import User, Department, Position, Organization, Status
from django.contrib.auth.hashers import make_password
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

# Настройка логирования в файл
logging.basicConfig(filename='load_employees.log', level=logging.INFO, format='%(asctime)s %(message)s')

API_BASE_URL = "https://toolssed.telecom.kz/API/HR-api.nsf/api.xsp"
EMPLOYEES_ENDPOINT = f"{API_BASE_URL}/1.3/empl/empl"
ORG_ENDPOINT = f"{API_BASE_URL}/1.2/org-structure"
USERNAME = "pot bsf"
PASSWORD = "potbsf"
DEFAULT_PASSWORD_HASH = make_password("123456")  # Предварительно вычисленный хеш пароля

class Command(BaseCommand):
    help = "Загружает сотрудников из внешней системы. Используйте --full для принудительной перезагрузки."

    def add_arguments(self, parser):
        parser.add_argument('--full', action='store_true', help='Игнорировать существующих сотрудников и перезагружаем всех.')

    def optimize_sqlite(self):
        """Оптимизация настроек SQLite для ускорения транзакций."""
        if 'sqlite' in connection.settings_dict['ENGINE']:
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA synchronous = OFF;")
                cursor.execute("PRAGMA journal_mode = WAL;")
                logging.info("SQLite оптимизирован: synchronous=OFF, journal_mode=WAL")

    def check_tables(self):
        """Проверяет наличие необходимых таблиц в базе данных."""
        required_tables = ['user_organization', 'user_user', 'user_department', 'user_position', 'user_status']
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                existing_tables = [row[0] for row in cursor.fetchall()]
                for table in required_tables:
                    if table not in existing_tables:
                        self.stdout.write(self.style.ERROR(f"❌ Таблица {table} не найдена. Выполните миграции!"))
                        raise CommandError(f"Таблица {table} отсутствует. Выполните 'python manage.py migrate'.")
        except OperationalError as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка проверки таблиц: {e}"))
            logging.error(f"Ошибка проверки таблиц: {e}")
            raise CommandError("Не удалось проверить таблицы. Убедитесь, что база данных настроена.")

    def get_auth_headers(self):
        raw = f"{USERNAME}:{PASSWORD}"
        b64 = base64.b64encode(raw.encode()).decode()
        return {
            "Authorization": f"Basic {b64}",
            "Accept": "application/json"
        }

    def create_session(self):
        """Создаёт сессию с повторными попытками при таймаутах."""
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session

    def fetch_organizations(self):
        headers = self.get_auth_headers()
        session = self.create_session()
        try:
            response = session.get(ORG_ENDPOINT, headers=headers, timeout=60)
            self.stdout.write(f"Статус код API организаций: {response.status_code}")
            logging.info(f"Статус код API организаций: {response.status_code}")
            if response.status_code != 200:
                self.stdout.write(f"Сырой ответ API организаций: {response.text[:500]}")
                logging.info(f"Сырой ответ API организаций: {response.text[:500]}")
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                self.stdout.write(self.style.ERROR(f"❌ Неверный Content-Type для организаций: {content_type}"))
                logging.error(f"Неверный Content-Type для организаций: {content_type}")
                return []

            data = response.json()
            if isinstance(data, dict) and 'data' in data:
                data = data['data']
            org_list = data if isinstance(data, list) else []
            self.stdout.write(f"Загружено организаций из API: {len(org_list)}")
            logging.info(f"Загружено организаций из API: {len(org_list)}")
            return org_list

        except Exception as ex:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка при загрузке организаций: {ex}"))
            logging.error(f"Ошибка при загрузке организаций: {ex}")
            return []

    def fetch_employees(self, organization_id):
        """Загружает сотрудников для указанной организации без пагинации."""
        url = f"{EMPLOYEES_ENDPOINT}?OrganizationId={organization_id}"
        headers = self.get_auth_headers()
        session = self.create_session()
        try:
            response = session.get(url, headers=headers, timeout=120)
            self.stdout.write(f"Статус код API для орг {organization_id}: {response.status_code}")
            logging.info(f"Статус код API для орг {organization_id}: {response.status_code}")
            if response.status_code != 200:
                self.stdout.write(f"Сырой ответ API для орг {organization_id}: {response.text[:500]}")
                logging.info(f"Сырой ответ API для орг {organization_id}: {response.text[:500]}")
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                self.stdout.write(self.style.ERROR(f"❌ [{organization_id}] Неверный Content-Type: {content_type}"))
                logging.error(f"[{organization_id}] Неверный Content-Type: {content_type}")
                return []

            data = response.json()
            if isinstance(data, dict) and 'data' in data:
                data = data['data']
            emp_list = data if isinstance(data, list) else []
            self.stdout.write(f"Загружено сотрудников для орг {organization_id}: {len(emp_list)}")
            logging.info(f"Загружено сотрудников для орг {organization_id}: {len(emp_list)}")
            return emp_list

        except requests.exceptions.Timeout as timeout_err:
            self.stdout.write(self.style.ERROR(f"❌ Таймаут при загрузке сотрудников для орг {organization_id}: {timeout_err}"))
            logging.error(f"Таймаут при загрузке сотрудников для орг {organization_id}: {timeout_err}")
            return []
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 404:
                self.stdout.write(self.style.WARNING(f"⚠️ Сотрудники для организации {organization_id} не найдены (404)"))
                logging.warning(f"Сотрудники для организации {organization_id} не найдены (404)")
                return []
            self.stdout.write(self.style.ERROR(f"❌ HTTP ошибка при загрузке сотрудников для организации {organization_id}: {http_err}"))
            logging.error(f"HTTP ошибка при загрузке сотрудников для организации {organization_id}: {http_err}")
            return []
        except Exception as ex:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка при загрузке сотрудников для организации {organization_id}: {ex}"))
            logging.error(f"Ошибка при загрузке сотрудников для организации {organization_id}: {ex}")
            return []

    def process_departments(self, departments):
        """Обрабатывает департаменты без иерархии."""
        new_departments = []
        for dept in departments:
            dept_id = dept.get('UNID')
            dept_name = dept.get('Name', {}).get('RU') or dept.get('Name', {}).get('KZ') or 'Unknown'
            if dept_id and dept_name:
                new_departments.append({
                    'id': dept_id,
                    'name': dept_name
                })
                if 'department' in dept and isinstance(dept.get('department'), list):
                    new_departments.extend(self.process_departments(dept['department']))
        return new_departments

    def convert_date_format(self, date_str):
        """Преобразует дату из формата DD.MM.YYYY в YYYY-MM-DD."""
        if not date_str:
            return None
        try:
            parsed_date = datetime.strptime(date_str, "%d.%m.%Y")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Некорректный формат даты: {date_str}, ошибка: {e}"))
            logging.warning(f"Некорректный формат даты: {date_str}, ошибка: {e}")
            return None

    def validate_user_data(self, emp, departments, positions, statuses, full_mode=False):
        """Проверяет данные пользователя. В full_mode пропускает проверки уникальности."""
        login = emp.get('login')
        department_id = emp.get('department_id')
        position_id = emp.get('position_id')
        status_id = emp.get('status_id')
        email = emp.get('email')
        iin = emp.get('iin')

        if not full_mode:  # Проверки уникальности только в обычном режиме
            if User.objects.filter(login__iexact=login).exists():
                self.stdout.write(self.style.WARNING(f"⚠️ Логин {login} уже существует, пропуск"))
                logging.warning(f"Логин {login} уже существует, пропуск")
                return False, 'existing_user'
            if email and User.objects.filter(email__iexact=email).exists():
                self.stdout.write(self.style.WARNING(f"⚠️ Email {email} уже существует, пропуск"))
                logging.warning(f"Email {email} уже существует, пропуск")
                return False, 'existing_user'
            if iin and User.objects.filter(iin=iin).exists():
                self.stdout.write(self.style.WARNING(f"⚠️ IIN {iin} уже существует, пропуск"))
                logging.warning(f"IIN {iin} уже существует, пропуск")
                return False, 'existing_user'

        # Проверка внешних ключей (лог, но не пропуск в full_mode)
        if department_id and not departments.filter(id=department_id).exists():
            self.stdout.write(self.style.WARNING(f"⚠️ Некорректный department_id {department_id} для {login}"))
            logging.warning(f"Некорректный department_id {department_id} для {login}")
            if not full_mode:
                return False, 'invalid_fk'
        if position_id and not positions.filter(id=position_id).exists():
            self.stdout.write(self.style.WARNING(f"⚠️ Некорректный position_id {position_id} для {login}"))
            logging.warning(f"Некорректный position_id {position_id} для {login}")
            if not full_mode:
                return False, 'invalid_fk'
        if status_id and not statuses.filter(id=status_id).exists():
            self.stdout.write(self.style.WARNING(f"⚠️ Некорректный status_id {status_id} для {login}"))
            logging.warning(f"Некорректный status_id {status_id} для {login}")
            if not full_mode:
                return False, 'invalid_fk'

        return True, None

    def handle(self, *args, **options):
        full_mode = options['full']
        if full_mode:
            self.stdout.write(self.style.WARNING("⚠️ Режим --full: Игнорируем существующих сотрудников и перезагружаем всех!"))
            logging.warning("Режим --full: Игнорируем существующих сотрудников и перезагружаем всех!")
            try:
                self.stdout.write("Очистка существующих данных...")
                logging.info("Очистка существующих данных...")
                User.objects.all().delete()
                Department.objects.all().delete()
                Position.objects.all().delete()
                Status.objects.all().delete()
                Organization.objects.all().delete()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Ошибка при очистке базы: {e}"))
                logging.error(f"Ошибка при очистке базы: {e}")
                raise CommandError("Не удалось очистить базу данных.")

        # Оптимизация SQLite
        self.optimize_sqlite()

        # Проверка таблиц
        self.check_tables()

        result = {'all': 0, 'new': 0, 'skipped': 0}
        skipped_reasons = {'existing_user': 0, 'invalid_fk': 0, 'empty_login': 0, 'api_error': 0}

        # Загружаем организации из API
        org_data = self.fetch_organizations()
        if not org_data:
            self.stdout.write(self.style.ERROR("❌ Не удалось загрузить данные об организациях. Завершение работы."))
            logging.error("Не удалось загрузить данные об организациях. Завершение работы.")
            return

        with transaction.atomic():
            for org in org_data:
                org_id = org.get('UNID') or org.get('BIN')
                org_name = org.get('Name', {}).get('RU') or org.get('Name', {}).get('KZ') or 'Unknown'
                if org_id:
                    try:
                        Organization.objects.get_or_create(id=org_id, defaults={'name': org_name})
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"❌ Ошибка сохранения организации {org_id}: {e}"))
                        logging.error(f"Ошибка сохранения организации {org_id}: {e}")
            self.stdout.write(f"Сохраненные организации: {list(Organization.objects.values('id', 'name'))}")
            logging.info(f"Сохраненные организации: {list(Organization.objects.values('id', 'name'))}")

        # Проверяем наличие организаций
        organizations = Organization.objects.all()
        self.stdout.write(f"Найдено организаций в базе: {organizations.count()}")
        logging.info(f"Найдено организаций в базе: {organizations.count()}")

        # Список исключённых организаций
        excluded_org_ids = [
            "91FE2BD7C184A34C462581DE0038F3DB",
            "CF988DA64851FA58462581DE00335CEE",
            "F5B8DB7C62BDE793462581E50020507F",
            "AF5B991D36CA7E47462581DE0078E553",
            "1AC4DF5ABE3EBC0A462581E2004342FF",
        ]
        organizations = organizations.exclude(id__in=excluded_org_ids)
        self.stdout.write(f"Организации после исключения: {organizations.count()}")
        logging.info(f"Организации после исключения: {organizations.count()}")

        # Загружаем существующие данные из базы
        db_employees = User.objects.all()
        self.stdout.write(f"Существующих сотрудников в базе: {db_employees.count()}")
        logging.info(f"Существующих сотрудников в базе: {db_employees.count()}")
        departments = Department.objects.all()
        positions = Position.objects.all()
        statuses = Status.objects.all()

        # Получаем существующие ID для оптимизации
        existing_dept_ids = set(departments.values_list('id', flat=True))
        existing_pos_ids = set(positions.values_list('id', flat=True))
        existing_status_ids = set(statuses.values_list('id', flat=True))
        new_departments = []
        new_positions = []
        new_statuses = []
        all_new_employees = []

        for org in organizations:
            self.stdout.write(f"🔍 Загружается организация {org.id} ({org.name})")
            logging.info(f"Загружается организация {org.id} ({org.name})")
            org_from_api = next((o for o in org_data if o.get('UNID') == org.id or o.get('BIN') == org.id), None)
            if org_from_api and 'department' in org_from_api:
                new_depts = self.process_departments(org_from_api['department'])
                new_departments.extend([d for d in new_depts if d['id'] not in existing_dept_ids])

            employees = self.fetch_employees(org.id)
            if not employees:
                skipped_reasons['api_error'] += 1
                continue

            for emp in employees:
                result['all'] += 1
                if not isinstance(emp, dict):
                    self.stdout.write(self.style.WARNING(f"Пропуск некорректных данных сотрудника: {emp} (тип: {type(emp)})"))
                    logging.warning(f"Пропуск некорректных данных сотрудника: {emp} (тип: {type(emp)})")
                    skipped_reasons['api_error'] += 1
                    result['skipped'] += 1
                    continue

                login = emp.get("Login", "").split("@")[0].lower()
                if not login:
                    self.stdout.write(self.style.WARNING(f"Пропуск сотрудника с пустым логином"))
                    logging.warning(f"Пропуск сотрудника с пустым логином")
                    skipped_reasons['empty_login'] += 1
                    result['skipped'] += 1
                    continue

                department = emp.get("Department")
                position = emp.get("Position")
                status = emp.get("Status")
                emails = emp.get("Email", [])
                corporate_email = next((e['address'] for e in emails if e.get('type') == 'corporate'), f"{login}@example.com")

                # Добавляем новые департаменты, должности, статусы
                if department and isinstance(department, dict) and department.get("id"):
                    dept_id = department["id"]
                    if dept_id not in existing_dept_ids and not any(d['id'] == dept_id for d in new_departments):
                        new_departments.append({'id': dept_id, 'name': department.get('name', 'Unknown')})

                if position and isinstance(position, dict) and position.get("name"):
                    pos_name = position["name"]
                    pos_id = position.get("id") or pos_name
                    if pos_id not in existing_pos_ids and not any(p['id'] == pos_id for p in new_positions):
                        new_positions.append({'id': pos_id, 'name': pos_name})

                if status and isinstance(status, dict) and status.get("id"):
                    status_id = status["id"]
                    if status_id not in existing_status_ids and not any(s['id'] == status_id for s in new_statuses):
                        new_statuses.append({'id': status_id, 'name': status.get('name', 'Unknown')})

                try:
                    birth_date = emp.get("BirthDate", "")
                    formatted_birth_date = self.convert_date_format(birth_date)

                    new_user = {
                        'login': login,
                        'last_name': emp.get("LastName", ""),
                        'first_name': emp.get("FirstName", ""),
                        'middle_name': emp.get("MiddleName", ""),
                        'iin': emp.get("IIN", ""),
                        'email': corporate_email,
                        'personnel_number': emp.get("PersonnelNumber", ""),
                        'birth_date': formatted_birth_date,
                        'is_mol': emp.get("isMOL", False),
                        'server': emp.get("Server", ""),
                        'department_id': department.get("id") if department else None,
                        'position_id': position.get("id") or position.get("name") if position else None,
                        'status_id': status.get("id") if status else None,
                        'organization': org,
                        'role': User.ROLES.GUEST,
                    }

                    is_valid, reason = self.validate_user_data(new_user, departments, positions, statuses, full_mode)
                    if is_valid:
                        all_new_employees.append(new_user)
                    else:
                        skipped_reasons[reason] += 1
                        result['skipped'] += 1
                except Exception as save_err:
                    self.stdout.write(self.style.ERROR(f"❌ Ошибка подготовки данных для {login}: {save_err}"))
                    logging.error(f"Ошибка подготовки данных для {login}: {save_err}")
                    skipped_reasons['api_error'] += 1
                    result['skipped'] += 1

        # Сохранение новых департаментов, должностей, статусов
        with transaction.atomic():
            if new_departments:
                self.stdout.write(f"Добавление {len(new_departments)} новых департаментов")
                logging.info(f"Добавление {len(new_departments)} новых департаментов")
                try:
                    Department.objects.bulk_create([Department(**dept) for dept in new_departments], ignore_conflicts=True)
                    existing_dept_ids.update([d['id'] for d in new_departments])
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Ошибка департаментов: {e}"))
                    logging.error(f"Ошибка департаментов: {e}")

            if new_positions:
                self.stdout.write(f"Добавление {len(new_positions)} новых должностей")
                logging.info(f"Добавление {len(new_positions)} новых должностей")
                try:
                    Position.objects.bulk_create([Position(**pos) for pos in new_positions], ignore_conflicts=True)
                    existing_pos_ids.update([p['id'] for p in new_positions])
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Ошибка должностей: {e}"))
                    logging.error(f"Ошибка должностей: {e}")

            if new_statuses:
                self.stdout.write(f"Добавление {len(new_statuses)} новых статусов")
                logging.info(f"Добавление {len(new_statuses)} новых статусов")
                try:
                    Status.objects.bulk_create([Status(**status) for status in new_statuses], ignore_conflicts=True)
                    existing_status_ids.update([s['id'] for s in new_statuses])
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Ошибка статусов: {e}"))
                    logging.error(f"Ошибка статусов: {e}")

        # Обновляем списки
        departments = Department.objects.all()
        positions = Position.objects.all()
        statuses = Status.objects.all()

        # Создание пользователей (по батчам по 1000 для скорости)
        new_users = []
        batch_size = 1000
        with transaction.atomic():
            for i, emp in enumerate(all_new_employees):
                try:
                    user = User(
                        login=emp['login'],
                        last_name=emp['last_name'],
                        first_name=emp['first_name'],
                        middle_name=emp['middle_name'],
                        iin=emp['iin'],
                        email=emp['email'],
                        personnel_number=emp['personnel_number'],
                        birth_date=emp['birth_date'],
                        is_mol=emp['is_mol'],
                        server=emp['server'],
                        department_id=emp['department_id'],
                        position_id=emp['position_id'],
                        status_id=emp['status_id'],
                        organization=emp['organization'],
                        role=emp['role'],
                        password=DEFAULT_PASSWORD_HASH,  # Используем предварительно вычисленный хеш
                    )
                    new_users.append(user)
                    result['new'] += 1

                    # Создаём батч
                    if len(new_users) >= batch_size or i == len(all_new_employees) - 1:
                        try:
                            User.objects.bulk_create(new_users, ignore_conflicts=not full_mode)
                            self.stdout.write(f"Успешно добавлено батч: {len(new_users)} пользователей")
                            logging.info(f"Успешно добавлено батч: {len(new_users)} пользователей")
                            new_users = []
                        except IntegrityError as e:
                            self.stdout.write(self.style.ERROR(f"❌ Ошибка батча (дубликаты): {e}"))
                            logging.error(f"Ошибка батча (дубликаты): {e}")
                            if full_mode:
                                for u in new_users:
                                    try:
                                        u.save()
                                    except Exception as ue:
                                        self.stdout.write(self.style.WARNING(f"⚠️ Пропуск пользователя {u.login}: {ue}"))
                                        logging.warning(f"Пропуск пользователя {u.login}: {ue}")
                                        result['skipped'] += 1
                                        skipped_reasons['invalid_data'] += 1
                            new_users = []
                except Exception as save_err:
                    self.stdout.write(self.style.ERROR(f"❌ Ошибка подготовки {emp['login']}: {save_err}"))
                    logging.error(f"Ошибка подготовки {emp['login']}: {save_err}")
                    result['skipped'] += 1
                    skipped_reasons['invalid_data'] += 1

        # Итоговый отчёт
        self.stdout.write(f"ИТОГО: Обработано {result['all']}, Добавлено {result['new']}, Пропущено {result['skipped']}")
        logging.info(f"ИТОГО: Обработано {result['all']}, Добавлено {result['new']}, Пропущено {result['skipped']}")
        self.stdout.write(f"Причины пропусков: existing_user={skipped_reasons['existing_user']}, invalid_fk={skipped_reasons['invalid_fk']}, empty_login={skipped_reasons['empty_login']}, api_error={skipped_reasons['api_error']}")
        logging.info(f"Причины пропусков: existing_user={skipped_reasons['existing_user']}, invalid_fk={skipped_reasons['invalid_fk']}, empty_login={skipped_reasons['empty_login']}, api_error={skipped_reasons['api_error']}")
        if result['new'] < result['all'] * 0.8:
            self.stdout.write(self.style.ERROR("❌ Обработано менее 80% — проверьте логи пропусков!"))
            logging.error("Обработано менее 80% — проверьте логи пропусков!")