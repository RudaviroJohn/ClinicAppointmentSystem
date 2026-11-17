
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from contextlib import AbstractContextManager
from enum import Enum
from typing import Optional, Tuple


P: int = 2  # Adjust to your assigned student/pair number (e.g., 0, 1, 2, or 3)


# 1. CLOCK (Deterministic virtual time, 0..168 hours)


class Clock(ABC):
    """Abstract clock interface providing the current hour (0..168)."""

    @abstractmethod
    def now(self) -> int:
        """Return the current simulated hour in the range 0..168."""
        raise NotImplementedError


class FakeClock(Clock):
    """Controllable clock used for deterministic demonstrations and testing."""

    def __init__(self, initial_hour: int = 0):
        self._hour = 0
        self.set(initial_hour)

    def set(self, hour: int) -> None:
        if not (0 <= hour <= 168):
            raise ValueError(f"Clock hour must be in range 0..168. Got: {hour}")
        self._hour = hour

    def advance(self, hours: int = 1) -> None:
        self.set(self._hour + hours)

    def now(self) -> int:
        return self._hour


# 2. LOGGING (Context Manager guaranteeing single open/close cycle)


class AppointmentLog(AbstractContextManager):
    """
    Context manager that guarantees the log file is opened and closed
    exactly once per Clinic session, even in the event of mid-operation exceptions.
    """

    def __init__(self, filename: str = "appointment.log"):
        self.filename = filename
        self._file = None
        self._opened = False
        self._closed = False

    def __enter__(self):
        if self._opened:
            raise RuntimeError("Log session has already been opened.")
        self._file = open(self.filename, "a", encoding="utf-8")
        self._opened = True
        print("[log] opened")
        self._file.write("[log] opened\n")
        self._file.flush()
        return self

    def write(self, message: str) -> None:
        if not self._opened or self._closed:
            raise RuntimeError("Cannot write to log: session is not open.")
        print(message)
        self._file.write(message + "\n")
        self._file.flush()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._opened and not self._closed:
            try:
                self._file.write("[log] closed\n")
                self._file.flush()
            finally:
                self._file.close()
                self._closed = True
                print("[log] closed")
        # Do not suppress unhandled exceptions
        return False


# 3. PEOPLE HIERARCHY & COOPERATIVE MULTIPLE INHERITANCE


class Person(ABC):
  
    constructor_count = 0

    def __init__(self, name: str, person_id: int, **kwargs):
        super().__init__(**kwargs)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Person name cannot be empty or whitespace.")
        if not isinstance(person_id, int) or person_id <= 0:
            raise ValueError(f"Person id must be a positive integer. Got: {person_id}")
        self._name = name.strip()
        self._id = person_id
        Person.constructor_count += 1

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> int:
        return self._id

    @abstractmethod
    def role(self) -> str:
        """Return the person's clinical or institutional role."""
        pass


class Patient(Person):
    """A clinic patient with category-based discount rate and emergency status."""

    def __init__(self, name: str, person_id: int, patient_type: str = "visitor", emergency: bool = False, **kwargs):
        super().__init__(name=name, person_id=person_id, **kwargs)
        valid_types = {"student", "staff-member", "visitor"}
        if patient_type not in valid_types:
            raise ValueError(f"Patient type must be one of {valid_types}. Got: {patient_type}")
        self._patient_type = patient_type
        self._emergency = emergency

    def role(self) -> str:
        return "Patient"

    @property
    def patient_type(self) -> str:
        return self._patient_type

    @property
    def emergency(self) -> bool:
        return self._emergency

    def flag_emergency(self, value: bool = True) -> None:
        self._emergency = bool(value)

    def discount_rate(self) -> float:
        """
        Polymorphic discount lookup.
        Student: 50% discount (0.50)
        Staff-member: 100% discount (1.00)
        Visitor: 0% discount (0.00)
        """
        discounts = {
            "student": 0.50,
            "staff-member": 1.00,
            "visitor": 0.00
        }
        return discounts[self._patient_type]


class Staff(Person, ABC):
    """Abstract base class for clinic medical staff."""

    @abstractmethod
    def fee(self) -> int:
        """Return consultation fee."""
        pass

    def buffer_hours(self) -> int:
        """Required idle gap between appointments. Default is 0."""
        return 0


class Doctor(Staff):
    def fee(self) -> int:
        return 40 + 5 * (P % 5)

    def buffer_hours(self) -> int:
        return 2

    def role(self) -> str:
        return "Doctor"


class Nurse(Staff):
    def fee(self) -> int:
        return 10 + (P % 3)

    def buffer_hours(self) -> int:
        return 1

    def role(self) -> str:
        return "Nurse"


class Pharmacist(Staff):
    def fee(self) -> int:
        return 5

    def buffer_hours(self) -> int:
        return 0

    def role(self) -> str:
        return "Pharmacist"


# Cooperative multiple inheritance classes
class Lecturer(Person):
    """Academic lecturer with a module name."""

    def __init__(self, name: str, person_id: int, module_name: str, **kwargs):
        if not isinstance(module_name, str) or not module_name.strip():
            raise ValueError("Module name cannot be empty.")
        self._module_name = module_name.strip()
        super().__init__(name=name, person_id=person_id, **kwargs)

    @property
    def module_name(self) -> str:
        return self._module_name

    def role(self) -> str:
        return "Lecturer"


class MedicalLecturer(Doctor, Lecturer):
    """
    Simultaneously a Doctor and a Lecturer.
    Inherits fee() and buffer_hours() from Doctor.
    Cooperative super().__init__ ensures Person.__init__ executes exactly once.
    """

    def __init__(self, name: str, person_id: int, module_name: str):
        super().__init__(name=name, person_id=person_id, module_name=module_name)

    def role(self) -> str:
        return "Doctor and Lecturer"


# 4. APPOINTMENT SPECIFICATION & INVARIANTS


class Status(Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"



class Appointment:
    def __init__(self, appointment_id: int, patient: Patient, staff: Staff, start_hour: int, fee: float):
        if not (0 <= start_hour <= 167):
            raise ValueError(f"Appointment start hour must be between 0 and 167. Got: {start_hour}")
        self._id = appointment_id
        self._patient = patient
        self._staff = staff
        self._start_hour = start_hour
        self._fee = fee
        self._status = Status.PENDING
        self._cancel_reason: Optional[str] = None

    @property
    def id(self) -> int:
        return self._id

    @property
    def patient(self) -> Patient:
        return self._patient

    @property
    def staff(self) -> Staff:
        return self._staff

    @property
    def start_hour(self) -> int:
        return self._start_hour

    @property
    def fee(self) -> float:
        return self._fee

    @property
    def status(self) -> Status:
        return self._status

    @property
    def cancel_reason(self) -> Optional[str]:
        return self._cancel_reason

    def confirm(self) -> None:
        if self._status is not Status.PENDING:
            raise ValueError(f"Cannot confirm appointment in status {self._status.value}")
        self._status = Status.CONFIRMED

    def cancel(self, now: int, reason: str = "patient request") -> None:
        if self._status is Status.CANCELLED:
            raise ValueError("cancelled appointment can never return")
        if now >= self._start_hour:
            raise ValueError("appointment has already started")
        if self._status is Status.CONFIRMED and (self._start_hour - now < 2):
            raise ValueError("too late")
        self._status = Status.CANCELLED
        self._cancel_reason = reason


# 5. CLINIC ENGINE & INVARIANTS


class Clinic:
    def __init__(self, clock: Clock, log: AppointmentLog, twist: int = (P % 4)):
        if twist not in {0, 1, 2, 3}:
            raise ValueError(f"Twist must be 0, 1, 2, or 3. Got: {twist}")
        self._clock = clock
        self._log = log
        self._twist = twist
        self._people: dict[int, Person] = {}
        self._patients: dict[int, Patient] = {}
        self._staff: dict[int, Staff] = {}
        self._appointments: dict[int, Appointment] = {}
        self._waiting: dict[int, deque[Patient]] = defaultdict(deque)
        self._next_appointment_id = 1

    @property
    def twist(self) -> int:
        return self._twist

    def register_patient(self, patient: Patient) -> None:
        try:
            if patient.id in self._people:
                raise ValueError(f"duplicate person id {patient.id}")
            self._people[patient.id] = patient
            self._patients[patient.id] = patient
            self._log.write(f"REGISTERED {patient.role()} #{patient.id} ({patient.name})")
        except Exception as exc:
            self._log.write(f"FAILED register patient #{patient.id}: {exc}")
            raise

    def register_staff(self, staff: Staff) -> None:
        try:
            if staff.id in self._people:
                raise ValueError(f"duplicate person id {staff.id}")
            self._people[staff.id] = staff
            self._staff[staff.id] = staff
            self._log.write(f"REGISTERED {staff.role()} #{staff.id} ({staff.name})")
        except Exception as exc:
            self._log.write(f"FAILED register staff #{staff.id}: {exc}")
            raise

    def appointments(self) -> Tuple[Appointment, ...]:
        """Encapsulation: return an immutable tuple snapshot of appointments."""
        return tuple(self._appointments.values())

    def _has_direct_conflict(self, person_id: int, hour: int, is_staff: bool, ignore_appt_id: Optional[int] = None) -> bool:
        """Check if a specific patient or staff already has a non-cancelled booking at this hour."""
        for appt in self._appointments.values():
            if appt.id == ignore_appt_id or appt.status is Status.CANCELLED:
                continue
            if appt.start_hour == hour:
                target_id = appt.staff.id if is_staff else appt.patient.id
                if target_id == person_id:
                    return True
        return False

    def _has_buffer_conflict(self, staff: Staff, hour: int) -> bool:
        """
        Twist 2: Staff buffer check.
        Every appointment occupies [start_hour, start_hour + 1).
        A buffer gap 'G' means no other appointment may start within G hours
        after it ends or before it begins:
        |appt.start_hour - hour| <= buffer_hours
        """
        gap = staff.buffer_hours()
        if gap == 0:
            return False
        for appt in self._appointments.values():
            if appt.status is Status.CANCELLED or appt.staff.id != staff.id:
                continue
            # If gap == 2 and appt is at 20 (ends at 21), next start must be >= 23 or <= 17.
            # Thus, conflict exists if |20 - hour| <= 2 (hours 18, 19, 20, 21, 22 are blocked).
            if abs(appt.start_hour - hour) <= gap:
                return True
        return False

    def _calculate_price(self, patient: Patient, staff: Staff) -> float:
        """Twist 3: polymorphic appointment pricing based on staff fee and patient discount rate."""
        base_fee = staff.fee()
        if self._twist == 3:
            return round(base_fee * (1.0 - patient.discount_rate()), 2)
        return float(base_fee)

    def book(self, patient: Patient, staff: Staff, hour: int) -> Appointment:
        """
        Book an appointment.
        Validates registrations, hour boundaries, conflicts, staff buffer gaps, and emergency bumps.
        """
        try:
            if patient.id not in self._patients:
                raise ValueError(f"Patient #{patient.id} is not registered.")
            if staff.id not in self._staff:
                raise ValueError(f"Staff #{staff.id} is not registered.")
            if not (0 <= hour <= 167):
                raise ValueError(f"Booking hour must be between 0 and 167. Got: {hour}")

            # Check if patient already has an appointment at this hour
            if self._has_direct_conflict(patient.id, hour, is_staff=False):
                raise ValueError(f"Patient #{patient.id} already has an appointment at hour {hour}.")

            # Check staff schedule and handle Twist 1 (Emergency bumping)
            staff_conflict = self._has_direct_conflict(staff.id, hour, is_staff=True)
            if staff_conflict:
                if self._twist == 1 and patient.emergency:
                    # Find candidate appointment to bump
                    bump_target = next(
                        (a for a in self._appointments.values()
                         if a.staff.id == staff.id
                         and a.start_hour == hour
                         and a.status is not Status.CANCELLED),
                        None
                    )
                    if bump_target is not None and bump_target.status is Status.PENDING:
                        bump_target.cancel(self._clock.now(), reason="bumped")
                        self._log.write(f"CANCELLED #{bump_target.id}: bumped for emergency")
                    else:
                        raise ValueError("Emergency booking cannot bump a CONFIRMED appointment.")
                else:
                    raise ValueError(f"Staff #{staff.id} is already booked at hour {hour}.")

            # Twist 2: Buffer gap enforcement
            if self._twist == 2 and self._has_buffer_conflict(staff, hour):
                raise ValueError(f"Booking violates required {staff.buffer_hours()}-hour buffer for {staff.name}.")

            fee = self._calculate_price(patient, staff)
            appt = Appointment(self._next_appointment_id, patient, staff, hour, fee)
            self._appointments[appt.id] = appt
            self._next_appointment_id += 1

            self._log.write(
                f"BOOKED #{appt.id}: {patient.name} with {staff.name} "
                f"at hour {hour}, fee {appt.fee:.2f}, PENDING"
            )
            return appt
        except Exception as exc:
            self._log.write(f"FAILED booking: {exc}")
            raise

    def confirm(self, appointment_id: int) -> None:
        try:
            if appointment_id not in self._appointments:
                raise ValueError(f"Appointment #{appointment_id} does not exist.")
            appt = self._appointments[appointment_id]
            appt.confirm()
            self._log.write(f"CONFIRMED #{appointment_id}")
        except Exception as exc:
            self._log.write(f"FAILED confirm #{appointment_id}: {exc}")
            raise

    def cancel(self, appointment_id: int, reason: str = "patient request") -> None:
        try:
            if appointment_id not in self._appointments:
                raise ValueError(f"Appointment #{appointment_id} does not exist.")
            appt = self._appointments[appointment_id]
            appt.cancel(self._clock.now(), reason=reason)
            self._log.write(f"CANCELLED #{appointment_id}: {reason}")

            # Twist 0: Automatic waiting list reallocation
            if self._twist == 0:
                self._offer_waiting_patient(appt.staff, appt.start_hour)
        except Exception as exc:
            self._log.write(f"FAILED cancel #{appointment_id}: {exc}")
            raise

    def join_waiting_list(self, patient: Patient, staff: Staff) -> None:
        """Twist 0: Register a patient onto a staff member's waiting queue."""
        try:
            if self._twist != 0:
                raise ValueError("Waiting list is only active for Twist 0.")
            if patient.id not in self._patients or staff.id not in self._staff:
                raise ValueError("Both patient and staff must be registered.")
            self._waiting[staff.id].append(patient)
            self._log.write(f"WAITLIST: Patient #{patient.id} joined waiting list for {staff.name} (#{staff.id})")
        except Exception as exc:
            self._log.write(f"FAILED waitlist: {exc}")
            raise

    def _offer_waiting_patient(self, staff: Staff, hour: int) -> Optional[Appointment]:
        """Twist 0: Offer newly released slot to first waiting patient without conflicts."""
        queue = self._waiting[staff.id]
        inspected = 0
        total = len(queue)
        while inspected < total:
            patient = queue.popleft()
            inspected += 1
            if not self._has_direct_conflict(patient.id, hour, is_staff=False):
                fee = self._calculate_price(patient, staff)
                appt = Appointment(self._next_appointment_id, patient, staff, hour, fee)
                self._appointments[appt.id] = appt
                self._next_appointment_id += 1
                self._log.write(
                    f"WAITLIST OFFER: new PENDING appointment #{appt.id} "
                    f"for patient #{patient.id} with {staff.name} at hour {hour}"
                )
                return appt
            queue.append(patient)  # Re-enqueue if conflict exists
        self._log.write(f"WAITLIST: No conflict-free patient found for {staff.name} at hour {hour}")
        return None

    def print_staff_fees(self) -> None:
        """
        Prints each staff member's role and fee in one polymorphic loop.
        Contains no isinstance/type tags; works seamlessly with newly added Staff types.
        """
        for member in self._staff.values():
            print(f"{member.role()}: ${member.fee()}")



# 6. MAIN DEMONSTRATION & TEST HARNESS


def main():
    print("=" * 70)
    print(f"CLINIC APPOINTMENT SYSTEM DEMO (Configured with P = {P}, Twist = {P % 4})")
    print("=" * 70)

    clock = FakeClock(initial_hour=10)

    with AppointmentLog("appointment.log") as log:
        clinic = Clinic(clock, log, twist=(P % 4))

        # 1. Register Staff & Patients
        print("\n--- 1. Registering Staff and Patients ---")
        p1 = Patient("Tariro Moyo", 1, patient_type="student")
        p2 = Patient("Kundai Sithole", 2, patient_type="visitor")
        p3 = Patient("Farai Shumba", 3, patient_type="staff-member")

        doc = Doctor("Dr. Chipo Ndlovu", 101)
        nurse = Nurse("Nurse Tendai Dube", 102)
        pharm = Pharmacist("Pharm. Rutendo Gumbo", 103)

        for person in [p1, p2, p3]:
            clinic.register_patient(person)
        for staff in [doc, nurse, pharm]:
            clinic.register_staff(staff)

        # 2. Polymorphic Staff Fee Loop (No isinstance/type tags)
        print("\n--- 2. Staff Roles and Fees (Polymorphic Loop) ---")
        clinic.print_staff_fees()

        # 3. Booking and Confirming
        print("\n--- 3. Standard Booking and Confirmation ---")
        appt1 = clinic.book(p1, doc, hour=20)
        clinic.confirm(appt1.id)

        # 4. Deliberate Failure: 2-Hour Cancellation Rule (Prompt Question 4)
        print("\n--- 4. Deliberate Failure Demo (Too Late to Cancel) ---")
        clock.set(19)  # 19 is only 1 hour before start_hour 20 (< 2 hours)
        try:
            print(f"Attempting to cancel #{appt1.id} at hour {clock.now()} (start is {appt1.start_hour})...")
            clinic.cancel(appt1.id)
        except ValueError as err:
            print(f"Caught expected error: {err}")

        # 5. Multiple Inheritance Verification (MedicalLecturer)
        print("\n--- 5. Cooperative Multiple Inheritance (MedicalLecturer) ---")
        count_before = Person.constructor_count
        med_lec = MedicalLecturer("Dr. Blessing Mutasa", 201, module_name="HCS301-Clinical")
        count_after = Person.constructor_count
        runs = count_after - count_before
        print(f"Created: {med_lec.name}")
        print(f"Role: {med_lec.role()}")
        print(f"Fee: ${med_lec.fee()}")
        print(f"Module: {med_lec.module_name}")
        print(f"Person constructor calls: {runs} (Expected: 1)")
        assert runs == 1, f"Expected 1 call to Person.__init__, got {runs}"

        # 6. Twist Demonstrations
        
        active_twist = clinic.twist
        print(f"\n--- 6. Active Twist Demonstration (Twist {active_twist}) ---")

        if active_twist == 0:
            print("Demonstrating Twist 0 (Waiting List):")
            clinic.join_waiting_list(p2, doc)
            clock.set(12)
            temp_appt = clinic.book(p3, doc, hour=25)
            print("Cancelling appointment to trigger automatic waiting list offer...")
            clinic.cancel(temp_appt.id, reason="slot released")

        elif active_twist == 1:
            print("Demonstrating Twist 1 (Emergency Bumping):")
            clock.set(12)
            pending_appt = clinic.book(p2, doc, hour=30)  # PENDING
            print(f"Created PENDING appointment #{pending_appt.id} for visitor.")
            emer_patient = Patient("Emergency Case", 99, patient_type="visitor", emergency=True)
            clinic.register_patient(emer_patient)
            print("Booking emergency patient at same hour (should bump PENDING)...")
            emer_appt = clinic.book(emer_patient, doc, hour=30)
            print(f"Emergency booking confirmed: #{emer_appt.id}")

        elif active_twist == 2:
            print(f"Demonstrating Twist 2 (Buffer Gaps): Doctor buffer = {doc.buffer_hours()} hrs")
            print("Existing appointment is at hour 20.")
            print("Attempting to book Doctor at hour 21 (within buffer gap)...")
            try:
                clinic.book(p2, doc, hour=21)
            except ValueError as err:
                print(f"Caught expected buffer conflict: {err}")
            print("Attempting valid booking at hour 23 (2-hour buffer respected)...")
            valid_appt = clinic.book(p2, doc, hour=23)
            print(f"Successfully booked #{valid_appt.id} at hour {valid_appt.start_hour}")
                      

        elif active_twist == 3:
            print("Demonstrating Twist 3 (Polymorphic Patient Discounts):")
            student_appt = clinic.book(p1, pharm, hour=40)
            visitor_appt = clinic.book(p2, pharm, hour=41)
            staff_appt = clinic.book(p3, pharm, hour=42)
            print(f"Pharmacist Base Fee: ${pharm.fee()}")
            print(f"Student fee (50% off): ${student_appt.fee:.2f}")
            print(f"Visitor fee (0% off):  ${visitor_appt.fee:.2f}")
            print(f"Staff fee (100% off):  ${staff_appt.fee:.2f}")

        # 7. Summary snapshot of appointments
        print("\n--- 7. Final Appointment Snapshot ---")
        for a in clinic.appointments():
            print(f"ID #{a.id} | Hour: {a.start_hour:03d} | Patient: {a.patient.name:<18} | "
                  f"Staff: {a.staff.name:<20} | Status: {a.status.value:<9} | Fee: ${a.fee:.2f}")

    print("\n[log] session exited cleanly. appointment.log updated.")
    print("=" * 70)


if __name__ == "__main__":
    main()
    