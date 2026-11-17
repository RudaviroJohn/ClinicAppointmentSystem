# Clinic Appointment System (Java 17+)

## 1. Classes & Diagram
**Classes:** `Person`, `Patient`, `Staff`, `Doctor`, `Nurse`, `Pharmacist`, `Lecturer` (interface), `MedicalLecturer`, `Appointment`, `Clinic`, `Clock` (interface), `FakeClock`, `AppointmentLog`, `Status`.

```
                         Person (abstract)
                         /              \
                    Patient          Staff (abstract)
                                      /    |      \
                                  Doctor  Nurse  Pharmacist
                                    |
     Lecturer (interface)           |
          ^                         |
          \------------------- MedicalLecturer
```

## 2. Encapsulation, Validation & State Transitions
- **Encapsulation:** All fields are `private final` (or `private` mutable state) with read-only getters. Internal collections are never handed out; `Clinic.getAppointments()` returns `Collections.unmodifiableList()`.
- **Validation:** `Person` constructor checks `name == null || name.trim().isEmpty()` and `id <= 0`, throwing `IllegalArgumentException`.
- **Transitions:**
  - `PENDING -> CONFIRMED`
  - `PENDING -> CANCELLED` (before start hour)
  - `CONFIRMED -> CANCELLED` ($\ge 2$ hours before start)
  - `CANCELLED` is terminal (cannot return).
- **Invariants:** Documented as Javadoc comments above `Appointment` and `Clinic` in `ClinicAppointmentSystem.java`.

## 3. Staff Fees & Polymorphism
- **Fees:** Doctor: $40 + 5 \times (P \bmod 5)$, Nurse: $10 + (P \bmod 3)$, Pharmacist: $5$.
- **Polymorphism:** `Clinic.printStaffFees()` loops over `Staff` and invokes `member.role()` and `member.fee()`. No `instanceof` or type tags are used. New subclasses can be added without modifying the loop or `Clinic`.

## 4. Logging
- **Mechanism:** `AutoCloseable` with `try-with-resources`.
- **Guarantee:** `[log] opened` prints/writes on open; `[log] closed` prints/writes on close via a `finally` block even when errors occur. Failed operations are logged as `FAILED <action>: <reason>`.

## 5. Diamond Inheritance & Interface Restructuring
- In Java, multiple class inheritance is prohibited. `Lecturer` is restructured into an **interface** defining `getModuleName()`.
- `MedicalLecturer` extends `Doctor` and implements `Lecturer`.
- Because `MedicalLecturer` extends only one class (`Doctor`), `Person` constructor runs exactly once, confirmed by `Person.constructorCount`.
- `MedicalLecturer.fee()` returns `Doctor.fee()` because it inherits directly from `Doctor` and there is no separate lecturer fee.

## 6. Rules & Twist ($P \bmod 4$)
- **Rules:** Globally unique person IDs; no patient or staff member may have overlapping active appointments at the same hour.
- **Twists:**
  - `0 (Waiting list):` Clinic queues patients per staff and auto-offers cancelled slots to the first conflict-free waiting patient as `PENDING`.
  - `1 (Emergency):` Emergency patient can bump a `PENDING` appointment at the same hour (`CANCELLED: bumped`). Cannot bump `CONFIRMED`.
  - `2 (Buffer):` Staff gaps (Doctor: 2h, Nurse: 1h, Pharmacist: 0h) queried via polymorphic `staff.bufferHours()`.
  - `3 (Discounts):` Patient discounts (student: 50%, staff-member: 100%, visitor: 0%) queried via polymorphic `patient.discountRate()`.

## 7. Design Decision Log
- **D1 (2-hour rule location):** Inside `Appointment.cancel()`. It governs the appointment's own state transitions and keeps rules localized to the entity.
- **D2 (Clock testability):** An injected `FakeClock` allows setting simulated hours ($0 \dots 168$) deterministically. System clock cannot test future or rapid boundary cases reliably.
- **D3 (Adding Pharmacist):** Created `Pharmacist` extending `Staff` only. Nothing else changed; no code leaked into `Clinic`.
- **D4 (MedicalLecturer fee & constructor):** Returns doctor fee. Java's single class inheritance prevents duplicate `Person` construction. Without turning `Lecturer` into an interface, Java would not compile.
- **D5 (Log failure):** Exceptions during writing or closing propagate out of `try-with-resources` so the failure is surfaced rather than silently suppressed.
- **D6 (Twist rationale):**
  - *(0)* `Clinic` owns the waiting list because reallocation requires full schedule visibility.
  - *(1)* Confirmed bookings cannot be bumped because confirmation represents a binding guarantee.
  - *(2)* `bufferHours()` allows staff to declare their own gaps polymorphically without type checks.
  - *(3)* `discountRate()` lives in `Patient` to keep patient classification logic out of `Clinic`.

## 8. Run & Demo
Compile and run with JDK 17+:
```bash
javac ClinicAppointmentSystem.java
java ClinicAppointmentSystem
```
`main()` demonstrates registration, polymorphic fee loop, booking, 2-hour cancellation failure, interface inheritance counter = 1, and the active twist ($P \bmod 4$).