# Clinic Appointment System (Python 3)

## 1. Classes & Diagram

**Classes:** `Person`, `Patient`, `Staff`, `Doctor`, `Nurse`, `Pharmacist`, `Lecturer`, `MedicalLecturer`, `Appointment`, `Clinic`, `Clock`, `FakeClock`, `AppointmentLog`, `Status`.

```
                         Person (abstract)
                         /              \
                    Patient          Staff (abstract)
                                      /    |      \
                                  Doctor  Nurse  Pharmacist
                                    |
            Lecturer                |
                \                  /
                 MedicalLecturer

```

## 2. Encapsulation, Validation & State Transitions

* **Encapsulation:** All fields are private (`_var`) with read-only `@property` getters. Internal collections are never handed out; `Clinic.appointments()` returns an immutable `tuple` snapshot.

* **Validation:** `Person` constructor checks `not name.strip()` and `person_id <= 0`, raising `ValueError`.

* **Transitions:**

  * `PENDING -> CONFIRMED`

  * `PENDING -> CANCELLED` (before start hour)

  * `CONFIRMED -> CANCELLED` ($\ge 2$ hours before start)

  * `CANCELLED` is terminal (cannot return).

* **Invariants:** Stated as comments above `Appointment` and `Clinic` in `main.py`.

## 3. Staff Fees & Polymorphism

* **Fees:** Doctor: $40 + 5 \times (P \bmod 5)$, Nurse: $10 + (P \bmod 3)$, Pharmacist: $5$.

* **Polymorphism:** `Clinic.print_staff_fees()` loops over `Staff` and invokes `member.role()` and `member.fee()`. No `isinstance` or type tags are used. New subclasses can be added without modifying the loop or `Clinic`.

## 4. Logging

* **Mechanism:** Context manager (`AbstractContextManager` with `__enter__` and `__exit__`).

* **Guarantee:** `[log] opened` prints/writes on entry; `[log] closed` prints/writes on exit via a `finally` block even when errors occur. Failed operations are logged as `FAILED <action>: <reason>`.

## 5. Diamond Inheritance (MedicalLecturer)

* Uses cooperative multiple inheritance (`Doctor, Lecturer`).

* Python's C3 MRO and `super().__init__(**kwargs)` ensure `Person.__init__` runs exactly once (verified by `Person.constructor_count`).

* `MedicalLecturer.fee()` returns `Doctor.fee()` because `Doctor` precedes `Lecturer` in the inheritance order and no lecturer fee exists.

## 6. Rules & Twist ($P \bmod 4$)

* **Rules:** Globally unique person IDs; no patient or staff member may have overlapping active appointments at the same hour.

* **Twists:**

  * `0 (Waiting list):` Clinic queues patients per staff and auto-offers cancelled slots to the first conflict-free waiting patient as `PENDING`.

  * `1 (Emergency):` Emergency patient can bump a `PENDING` appointment at the same hour (`CANCELLED: bumped`). Cannot bump `CONFIRMED`.

  * `2 (Buffer):` Staff gaps (Doctor: 2h, Nurse: 1h, Pharmacist: 0h) queried via polymorphic `staff.buffer_hours()`.

  * `3 (Discounts):` Patient discounts (student: 50%, staff-member: 100%, visitor: 0%) queried via polymorphic `patient.discount_rate()`.

## 7. Design Decision Log

* **D1 (2-hour rule location):** Inside `Appointment.cancel()`. It governs the appointment's own state transitions and keeps rules localized to the entity.

* **D2 (Clock testability):** An injected `FakeClock` allows setting simulated hours ($0 \dots 168$) deterministically. System clock cannot test future or rapid boundary cases reliably.

* **D3 (Adding Pharmacist):** Created `Pharmacist(Staff)` only. Nothing else changed; no code leaked into `Clinic`.

* **D4 (MedicalLecturer fee & constructor):** Returns doctor fee. Cooperative `super()` prevents duplicate `Person` construction. Without it, `Person.__init__` would execute twice.

* **D5 (Log failure):** Write/close exceptions are allowed to propagate after cleanup so failures are not silently ignored.

* **D6 (Twist rationale):**

  * *(0)* `Clinic` owns the waiting list because reallocation requires full schedule visibility.

  * *(1)* Confirmed bookings cannot be bumped because confirmation represents a binding guarantee.

  * *(2)* `buffer_hours()` allows staff to declare their own gaps polymorphically without type checks.

  * *(3)* `discount_rate()` lives in `Patient` to keep patient classification logic out of `Clinic`.

## 8. Run & Demo

Run with Python 3.10+:

```
python main.py

```

`main()` demonstrates registration, polymorphic fee loop, booking, 2-hour cancellation failure, multiple inheritance counter, and the active twist ($P \bmod 4$).