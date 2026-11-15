
# Specification Driven Development Multi Agent

## Обзор

SDDMA (Spec Driven Development Multi Agent) — мультиагентная система для автоматизированной разработки программного обеспечения на основе формализованных спецификаций.

Система состоит из двух основных компонентов:

1. **Specification Driven Development Multi Agent Engine** — движок автоматизированной разработки, который преобразует спецификации проекта в работающий программный код. Он управляет графом зависимостей задач, координирует специализированных AI-агентов, организует реализацию, тестирование и исправление ошибок.

2. **Specification Builder** — компонент для интерактивного создания и редактирования спецификаций проекта с помощью LLM по принципу Human-in-the-Loop. Пользователь совместно с LLM формирует спецификацию поэтапно, согласовывает содержание каждого раздела и утверждает итоговый результат.

## Содержание

- [Specification Driven Development Multi Agent Engine](docs/engine.md)
  - [Структура спецификации проекта](docs/engine.md#структура-спецификации-проекта)
  - [Файловая структура](docs/engine.md#файловая-структура)
  - [Task](docs/engine.md#task)
  - [Состояние](docs/engine.md#состояние)
- [Агенты](docs/agents.md)
  - [Researcher](docs/agents.md#researcher)
  - [Implementer](docs/agents.md#implementer)
  - [Tester](docs/agents.md#tester)
  - [Fixer](docs/agents.md#fixer)
- [Компоненты движка](docs/components.md)
  - [Tool](docs/components.md#1-tool)
  - [Guardrails](docs/components.md#предохранители-guardrails)
  - [LLMClient](docs/components.md#2-llmclient)
  - [PromptProvider](docs/components.md#3-promptprovider)
  - [AgentRunner](docs/components.md#4-agent)
  - [TaskRunner](docs/components.md#5-taskrunner)
  - [WorkflowRunner](docs/components.md#6-workflowrunner)
- [Диаграммы активности раннеров](docs/activities/agent.md)
  - [AgentRunner](docs/activities/agent.md)
  - [TaskRunner](docs/activities/task.md)
  - [WorkflowRunner](docs/activities/workflow.md)
- [Диаграммы состояния для стейт машин](docs/fsms/agent.md)
  - [AgentFSM](docs/fsms/agent.md)
  - [TaskFSM](docs/fsms/task.md)
  - [WorkflowFSM](docs/fsms/workflow.md)
- [Specification Builder](docs/specification-builder.md)
- [REST API Specification Builder Backend](docs/rest-api.md)
- [Terminal User Interface](docs/tui.md)

## Структура проекта

```text
.
├── benchmarks/                    # Тестовые проекты для оценки качества разработки
│   └── shop/                      # Демонстрационный проект интернет-магазина
│       ├── AGENT.md               # Спецификация и инструкции для AI-агента
│       ├── AGENT.yaml             # Конфигурация AI-агента
│       ├── migrations/            # Миграции базы данных
│       │   └── 001_init.sql       # Начальная миграция схемы базы данных
│       ├── skills/                # Навыки, доступные AI-агентам
│       │   ├── fastapi-router/    # Навык разработки FastAPI-маршрутов
│       │   │   └── SKILL.md
│       │   ├── fastapi-router-testing/ # Навык тестирования FastAPI-маршрутов
│       │   │   └── SKILL.md
│       │   ├── service-implementing/ # Навык реализации бизнес-логики
│       │   │   └── SKILL.md
│       │   ├── sqlite-implementing/ # Навык реализации работы с SQLite
│       │   │   └── SKILL.md
│       │   ├── sqlite-testing/    # Навык тестирования SQLite
│       │   │   └── SKILL.md
│       │   └── testing-with-mocks/ # Навык модульного тестирования с моками
│       │       └── SKILL.md
│       ├── tasks/                 # Задачи для последовательной разработки проекта
│       │   ├── 001_products_repository.md
│       │   ├── 002_orders_repository.md
│       │   ├── 003_order_lines_repository.md
│       │   ├── 004_checkout_service.md
│       │   ├── 005_orders_router.md
│       │   └── 006_main.md
│       └── workflows/             # Сценарии выполнения связанных задач
│           └── end_to_end.md      # Сквозной сценарий разработки интернет-магазина
│
├── benchmark.sh                   # Скрипт запуска benchmark-тестирования
│
├── config/                        # Загрузка и управление конфигурацией
│   ├── config.py                  # Модели и логика конфигурации приложения
│   ├── config_test.py             # Тесты конфигурации
│   └── __init__.py                # Инициализация пакета
│
├── docs/                          # Документация проекта
│   ├── agents.md                  # Описание специализированных AI-агентов
│   ├── components.md              # Описание компонентов движка
│   ├── activities/                # Диаграммы процессов
│   │   ├── agent.md               # Диаграмма работы AI-агента
│   │   ├── task.md                # Диаграмма выполнения отдельной задачи
│   │   └── workflow.md            # Диаграмма выполнения рабочего процесса
│   ├── fsms/                      # Диаграммы состояний
│   │   ├── agent.md               # Диаграмма состояний AI-агента
│   │   ├── task.md                # Диаграмма состояний отдельной задачи
│   │   └── workflow.md            # Диаграмма состояний рабочего процесса
│   ├── engine.md                  # Описание движка автоматизированной разработки
│   ├── rest-api.md                # Спецификация REST API Specification Builder
│   ├── specification-builder.md   # Описание Specification Builder
│   └── tui.md                     # Описание терминального интерфейса
│
├── factories/                     # Фабрики создания компонентов
│   ├── agent.py                   # Фабрика создания AI-агентов
│   ├── agent_test.py              # Тесты фабрики AI-агентов
│   ├── __init__.py                # Инициализация пакета
│   ├── task.py                    # Фабрика создания задач
│   ├── task_test.py               # Тесты фабрики задач
│   ├── workflow.py                # Фабрика создания рабочих процессов
│   └── workflow_test.py           # Тесты фабрики рабочих процессов
│
├── fsms/                          # Конечные автоматы управления состояниями выполнения
│   ├── agent.py                   # FSM состояния AI-агента
│   ├── agent_test.py              # Тесты FSM AI-агента
│   ├── __init__.py                # Инициализация пакета
│   ├── task.py                    # FSM состояния задачи
│   ├── task_test.py               # Тесты FSM задачи
│   ├── workflow.py                # FSM состояния рабочего процесса
│   └── workflow_test.py           # Тесты FSM рабочего процесса
│
├── guardrails/                    # Предохранители, проверяющие допустимость действий агентов
│   ├── bash.py                    # Проверка безопасности команд Bash
│   ├── bash_test.py               # Тесты проверки команд Bash
│   ├── fqn_write.py               # Проверка записи только в разрешённый файл
│   ├── fqn_write_test.py          # Тесты проверки целевого файла
│   ├── __init__.py                # Инициализация пакета
│   ├── workspace.py               # Проверка допустимости операций в рабочей директории
│   └── workspace_test.py          # Тесты проверки рабочей директории
│
├── llm/                           # Интеграция с языковой моделью
│   ├── client.py                  # Клиент для взаимодействия с LLM
│   ├── client_test.py             # Тесты клиента LLM
│   └── __init__.py                # Инициализация пакета
│
├── main.py                        # Точка входа приложения
│
├── Makefile                       # Команды сборки, тестирования и разработки
│
├── models/                        # Модели данных и основные типы системы
│   ├── agent.py                   # Модели AI-агентов и их результатов
│   ├── graph.py                   # Модели графа зависимостей задач
│   ├── __init__.py                # Экспорт моделей пакета
│   ├── llm.py                     # Модели сообщений и метрик LLM
│   ├── skill.py                   # Модель навыка AI-агента
│   ├── state.py                   # Модель состояния выполнения задачи
│   ├── status.py                  # Статусы выполнения задач и тестирования
│   ├── task.py                    # Модели задач и результатов их выполнения
│   ├── test.py                    # Модели тестовых сценариев и результатов
│   ├── tool.py                   # Модели инструментов и вызовов инструментов
│   └── workflow.py                # Модели рабочих процессов и их результатов
│
├── parsers/                       # Разбор спецификаций и входных данных
│   ├── graph.py                   # Построение графа зависимостей из спецификации
│   ├── graph_test.py              # Тесты построения графа
│   ├── __init__.py                # Инициализация пакета
│   ├── skill.py                   # Загрузка и разбор описаний навыков
│   ├── skill_test.py              # Тесты загрузки навыков
│   ├── task.py                    # Разбор спецификаций задач
│   └── task_test.py               # Тесты разбора задач
│
├── promptproviders/               # Провайдеры системных и пользовательских промптов
│   ├── fixer.py                   # Формирование промптов для Fixer
│   ├── fixer_test.py              # Тесты промптов Fixer
│   ├── implementer.py             # Формирование промптов для Implementer
│   ├── implementer_test.py        # Тесты промптов Implementer
│   ├── __init__.py                # Инициализация пакета
│   ├── researcher.py              # Формирование промптов для Researcher
│   ├── researcher_test.py         # Тесты промптов Researcher
│   ├── tester.py                  # Формирование промптов для Tester
│   └── tester_test.py             # Тесты промптов Tester
│
├── prompts/                       # Шаблоны промптов специализированных агентов
│   ├── fixer.py                   # Промпты агента исправления ошибок
│   ├── implementer.py             # Промпты агента реализации
│   ├── __init__.py                # Инициализация пакета
│   ├── researcher.py              # Промпты агента исследования
│   └── tester.py                  # Промпты агента тестирования
│
├── runners/                       # Координаторы выполнения агентов, задач и рабочих процессов
│   ├── agent.py                   # Выполнение взаимодействия AI-агента с LLM и инструментами
│   ├── agent_test.py              # Тесты выполнения AI-агента
│   ├── __init__.py                # Инициализация пакета
│   ├── task.py                    # Координация выполнения отдельной задачи
│   ├── task_test.py               # Тесты координатора задач
│   ├── workflow.py                # Координация выполнения графа зависимых задач
│   └── workflow_test.py           # Тесты координатора рабочих процессов
│
├── tools/                         # Инструменты, доступные AI-агентам
│   ├── append.py                  # Инструмент добавления содержимого в файл
│   ├── append_test.py             # Тесты инструмента добавления содержимого
│   ├── bash.py                    # Инструмент выполнения команд Bash
│   ├── bash_test.py               # Тесты инструмента Bash
│   ├── __init__.py                # Инициализация пакета
│   ├── load_skill.py              # Инструмент загрузки навыков
│   ├── load_skill_test.py         # Тесты инструмента загрузки навыков
│   ├── patch.py                   # Инструмент изменения содержимого файла
│   ├── patch_test.py              # Тесты инструмента изменения содержимого
│   ├── read.py                    # Инструмент чтения файлов
│   └── read_test.py               # Тесты инструмента чтения файлов
│
├── pyproject.toml                 # Конфигурация проекта, зависимости и настройки инструментов
└── README.md                      # Основная документация и описание проекта
```

## TODO

### Specification Driven Development Multi Agent Engine

- [x] Конфигурация движка
- [x] Модели данных
- [x] Парсинг спецификаций задач
- [x] Парсинг графа зависимостей
- [x] Загрузка навыков (Skills)
- [x] LLM Client
- [x] Tool — система инструментов
- [x] Guardrails — предохранители вызова инструментов
- [x] PromptProvider — управление промптами
- [x] Researcher — исследование проекта
- [x] Implementer — реализация функциональности
- [x] Tester — проверка реализации
- [x] Fixer — исправление ошибок
- [x] AgentFSM — стейт машина агента
- [x] TaskFSM — стейт машина задчи
- [x] WorkflowFSM — стейт машина воркфлоу
- [x] AgentRunner — выполнение задач с помощью LLM
- [x] TaskRunner — координация выполнения задач
- [x] WorkflowRunner — управление графом зависимостей задач
- [x] Фабрики создания компонентов
- [x] Модульные тесты компонентов

### Specification Builder

- [ ] REST API Backend
- [ ] Terminal User Interface (TUI)

