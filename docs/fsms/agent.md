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
        Начальное состояние агента.
        Допускается запуск или сброс.
    end note

    note right of RUNNING
        Агент выполняет задачу.
        Допускается успешное завершение
        или переход в состояние ошибки.
    end note

    note right of SUCCESS
        Задача успешно выполнена.
        Для повторного запуска нужен reset().
    end note

    note right of ERROR
        При выполнении произошла ошибка.
        Для повторного запуска нужен reset().
    end note
```

[← Back to README](../../README.md)