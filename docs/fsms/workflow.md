[← Back to README](../../README.md)

```mermaid
stateDiagram-v2
    [*] --> IDLE

    IDLE --> RUNNING: mark_running()

    RUNNING --> SUCCESS: mark_success()
    RUNNING --> ERROR: mark_error()

    SUCCESS --> IDLE: reset()
    ERROR --> IDLE: reset()

    note right of IDLE
        Начальное состояние рабочего процесса.
        Допускается запуск или сброс.
    end note

    note right of RUNNING
        Рабочий процесс выполняется.
        Допускается успешное завершение
        или переход в состояние ошибки.
    end note

    note right of SUCCESS
        Все задачи рабочего процесса
        успешно завершены.
        Для повторного запуска нужен reset().
    end note

    note right of ERROR
        При выполнении рабочего процесса
        произошла ошибка.
        Для повторного запуска нужен reset().
    end note
```

[← Back to README](../../README.md)