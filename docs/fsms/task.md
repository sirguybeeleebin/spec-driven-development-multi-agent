[← Back to README](../../README.md)

```mermaid
stateDiagram-v2
    [*] --> IDLE

    IDLE --> RUNNING: mark_running()
    IDLE --> HOLD: mark_hold()

    RUNNING --> SUCCESS: mark_success()
    RUNNING --> ERROR: mark_error()
    RUNNING --> HOLD: mark_hold()

    SUCCESS --> IDLE: reset()
    ERROR --> IDLE: reset()
    HOLD --> IDLE: reset()

    note right of IDLE
        Начальное состояние задачи.
        Допускается запуск или приостановка.
    end note

    note right of RUNNING
        Задача выполняется.
        Допускается успешное завершение,
        завершение с ошибкой или приостановка.
    end note

    note right of HOLD
        Выполнение задачи приостановлено.
        Для повторного запуска нужен reset().
    end note

    note right of SUCCESS
        Задача успешно выполнена.
        Для повторного запуска нужен reset().
    end note

    note right of ERROR
        При выполнении задачи произошла ошибка.
        Для повторного запуска нужен reset().
    end note
```

[← Back to README](../../README.md)