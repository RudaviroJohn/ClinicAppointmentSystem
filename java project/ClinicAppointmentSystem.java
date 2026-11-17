
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;

public class ClinicAppointmentSystem {

    public static final int P = 2; 

    public interface Clock {
        int now();
    }

    public static class FakeClock implements Clock {
        private int hour;

        public FakeClock(int initialHour) {
            set(initialHour);
        }

        public void set(int newHour) {
            if (newHour < 0 || newHour > 168) {
                throw new IllegalArgumentException("Clock hour must be in range 0-168. Got: " + newHour);
            }
            this.hour = newHour;
        }

        public void advance(int hours) {
            set(this.hour + hours);
        }

        @Override
        public int now() {
            return this.hour;
        }
    }

    public static class AppointmentLog implements AutoCloseable {
        private final String filename;
        private BufferedWriter writer;
        private boolean opened = false;
        private boolean closed = false;

        public AppointmentLog(String filename) {
            this.filename = filename;
        }

        public AppointmentLog open() throws IOException {
            if (opened) {
                throw new IllegalStateException("Another Log session is open.");
            }
            this.writer = new BufferedWriter(new FileWriter(this.filename, true));
            this.opened = true;
            System.out.println("[log] opened");
            this.writer.write("[log] opened\n");
            this.writer.flush();
            return this;
        }

        public void write(String message) {
            if (!opened || closed) {
                throw new IllegalStateException("Cannot write to log because a session is not open.");
            }
            try {
                System.out.println(message);
                this.writer.write(message + "\n");
                this.writer.flush();
            } catch (IOException e) {
                throw new RuntimeException("There is a Disk write error occurred while logging: " + e.getMessage(), e);
            }
        }

        @Override
        public void close() throws IOException {
            if (opened && !closed) {
                try {
                    this.writer.write("[log] closed\n");
                    this.writer.flush();
                } finally {
                    this.writer.close();
                    this.closed = true;
                    System.out.println("[log] closed");
                }
            }
        }
    }

    public static abstract class Person {
        public static int constructorCount = 0;

        private final String name;
        private final int id;

        public Person(String name, int id) {
            if (name == null || name.trim().isEmpty()) {
                throw new IllegalArgumentException("Name cannot be empty or whitespace.");
            }
            if (id <= 0) {
                throw new IllegalArgumentException("Person id must be a positive integer. Got: " + id);
            }
            this.name = name.trim();
            this.id = id;
            constructorCount++;
        }

        public String getName() {
            return name;
        }

        public int getId() {
            return id;
        }

        public abstract String role();
    }

    public static class Patient extends Person {
        private final String patientType;
        private boolean emergency;

        public Patient(String name, int id, String patientType, boolean emergency) {
            super(name, id);
            if (!patientType.equals("student") && !patientType.equals("staff-member")
                    && !patientType.equals("visitor")) {
                throw new IllegalArgumentException(
                        "Patient type must be student, staff-member, or visitor. Got: " + patientType);
            }
            this.patientType = patientType;
            this.emergency = emergency;
        }

        public Patient(String name, int id, String patientType) {
            this(name, id, patientType, false);
        }

        @Override
        public String role() {
            return "Patient";
        }

        public String getPatientType() {
            return patientType;
        }

        public boolean isEmergency() {
            return emergency;
        }

        public void flagEmergency(boolean value) {
            this.emergency = value;
        }

        public double discountRate() {
            return switch (this.patientType) {
                case "student" -> 0.50;
                case "staff-member" -> 1.00;
                default -> 0.00;
            };
        }
    }

    public static abstract class Staff extends Person {
        public Staff(String name, int id) {
            super(name, id);
        }

        public abstract int fee();

        public int bufferHours() {
            return 0;
        }
    }

    public static class Doctor extends Staff {
        public Doctor(String name, int id) {
            super(name, id);
        }

        @Override
        public int fee() {
            return 40 + 5 * (P % 5);
        }

        @Override
        public int bufferHours() {
            return 2;
        }

        @Override
        public String role() {
            return "Doctor";
        }
    }

    public static class Nurse extends Staff {
        public Nurse(String name, int id) {
            super(name, id);
        }

        @Override
        public int fee() {
            return 10 + (P % 3);
        }

        @Override
        public int bufferHours() {
            return 1;
        }

        @Override
        public String role() {
            return "Nurse";
        }
    }

    public static class Pharmacist extends Staff {
        public Pharmacist(String name, int id) {
            super(name, id);
        }

        @Override
        public int fee() {
            return 5;
        }

        @Override
        public int bufferHours() {
            return 0;
        }

        @Override
        public String role() {
            return "Pharmacist";
        }
    }

    public interface Lecturer {
        String getModuleName();
    }

    public static class MedicalLecturer extends Doctor implements Lecturer {
        private final String moduleName;

        public MedicalLecturer(String name, int id, String moduleName) {
            super(name, id);
            if (moduleName == null || moduleName.trim().isEmpty()) {
                throw new IllegalArgumentException("Module name cannot be empty.");
            }
            this.moduleName = moduleName.trim();
        }

        @Override
        public String getModuleName() {
            return moduleName;
        }

        @Override
        public String role() {
            return "Doctor and Lecturer";
        }
    }


    public enum Status {
        PENDING,
        CONFIRMED,
        CANCELLED
    }

    public static class Appointment {
        private final int id;
        private final Patient patient;
        private final Staff staff;
        private final int startHour;
        private final double fee;
        private Status status;
        private String cancelReason;

        public Appointment(int id, Patient patient, Staff staff, int startHour, double fee) {
            if (startHour < 0 || startHour > 167) {
                throw new IllegalArgumentException(
                        "Appointment start hour must be between 0 and 167. Got: " + startHour);
            }
            this.id = id;
            this.patient = patient;
            this.staff = staff;
            this.startHour = startHour;
            this.fee = fee;
            this.status = Status.PENDING;
            this.cancelReason = null;
        }

        public int getId() {
            return id;
        }

        public Patient getPatient() {
            return patient;
        }

        public Staff getStaff() {
            return staff;
        }

        public int getStartHour() {
            return startHour;
        }

        public double getFee() {
            return fee;
        }

        public Status getStatus() {
            return status;
        }

        public String getCancelReason() {
            return cancelReason;
        }

        public void confirm() {
            if (this.status != Status.PENDING) {
                throw new IllegalStateException("Only a PENDING appointment can be confirmed.");
            }
            this.status = Status.CONFIRMED;
        }

        public void cancel(int now, String reason) {
            if (this.status == Status.CANCELLED) {
                throw new IllegalStateException("cancelled appointment can never return");
            }
            if (now >= this.startHour) {
                throw new IllegalStateException("appointment has already started");
            }
            if (this.status == Status.CONFIRMED && (this.startHour - now < 2)) {
                throw new IllegalStateException("too late");
            }
            this.status = Status.CANCELLED;
            this.cancelReason = reason;
        }
    }

    public static class Clinic {
        private final Clock clock;
        private final AppointmentLog log;
        private final int twist;

        private final Map<Integer, Person> people = new HashMap<>();
        private final Map<Integer, Patient> patients = new HashMap<>();
        private final Map<Integer, Staff> staff = new HashMap<>();
        private final Map<Integer, Appointment> appointments = new LinkedHashMap<>();
        private final Map<Integer, Deque<Patient>> waitingList = new HashMap<>();
        private int nextAppointmentId = 1;

        public Clinic(Clock clock, AppointmentLog log, int twist) {
            if (twist < 0 || twist > 3) {
                throw new IllegalArgumentException("Twist must be 0, 1, 2, or 3. Got: " + twist);
            }
            this.clock = clock;
            this.log = log;
            this.twist = twist;
        }

        public int getTwist() {
            return twist;
        }

        public void registerPatient(Patient patient) {
            try {
                if (people.containsKey(patient.getId())) {
                    throw new IllegalArgumentException("duplicate person id " + patient.getId());
                }
                people.put(patient.getId(), patient);
                patients.put(patient.getId(), patient);
                log.write("REGISTERED " + patient.role() + " #" + patient.getId() + " (" + patient.getName() + ")");
            } catch (Exception e) {
                log.write("FAILED register patient #" + patient.getId() + ": " + e.getMessage());
                throw e;
            }
        }

        public void registerStaff(Staff staffMember) {
            try {
                if (people.containsKey(staffMember.getId())) {
                    throw new IllegalArgumentException("duplicate person id " + staffMember.getId());
                }
                people.put(staffMember.getId(), staffMember);
                staff.put(staffMember.getId(), staffMember);
                log.write("REGISTERED " + staffMember.role() + " #" + staffMember.getId() + " (" + staffMember.getName()
                        + ")");
            } catch (Exception e) {
                log.write("FAILED register staff #" + staffMember.getId() + ": " + e.getMessage());
                throw e;
            }
        }

        public List<Appointment> getAppointments() {
            return Collections.unmodifiableList(new ArrayList<>(appointments.values()));
        }

        private boolean hasDirectConflict(int personId, int hour, boolean isStaff) {
            for (Appointment appt : appointments.values()) {
                if (appt.getStatus() == Status.CANCELLED)
                    continue;
                if (appt.getStartHour() == hour) {
                    int targetId = isStaff ? appt.getStaff().getId() : appt.getPatient().getId();
                    if (targetId == personId)
                        return true;
                }
            }
            return false;
        }

        private boolean hasBufferConflict(Staff staffMember, int hour) {
            int gap = staffMember.bufferHours();
            if (gap == 0)
                return false;
            for (Appointment appt : appointments.values()) {
                if (appt.getStatus() == Status.CANCELLED || appt.getStaff().getId() != staffMember.getId()) {
                    continue;
                }
                // If gap is G, starting at 'hour' conflicts if |appt.startHour - hour| <= G
                if (Math.abs(appt.getStartHour() - hour) <= gap) {
                    return true;
                }
            }
            return false;
        }

        private double calculatePrice(Patient patient, Staff staffMember) {
            double baseFee = staffMember.fee();
            if (this.twist == 3) {
                return Math.round(baseFee * (1.0 - patient.discountRate()) * 100.0) / 100.0;
            }
            return baseFee;
        }

        public Appointment book(Patient patient, Staff staffMember, int hour) {
            try {
                if (!patients.containsKey(patient.getId())) {
                    throw new IllegalArgumentException("Patient #" + patient.getId() + " is not registered.");
                }
                if (!staff.containsKey(staffMember.getId())) {
                    throw new IllegalArgumentException("Staff #" + staffMember.getId() + " is not registered.");
                }
                if (hour < 0 || hour > 167) {
                    throw new IllegalArgumentException("Hour must be between 0 and 167. Got: " + hour);
                }

                if (hasDirectConflict(patient.getId(), hour, false)) {
                    throw new IllegalStateException(
                            "Patient #" + patient.getId() + " already has an appointment at hour " + hour + ".");
                }

                if (hasDirectConflict(staffMember.getId(), hour, true)) {
                    if (this.twist == 1 && patient.isEmergency()) {
                        // Twist 1: Emergency booking can bump a PENDING appointment
                        Appointment bumpTarget = null;
                        for (Appointment a : appointments.values()) {
                            if (a.getStaff().getId() == staffMember.getId() && a.getStartHour() == hour
                                    && a.getStatus() != Status.CANCELLED) {
                                bumpTarget = a;
                                break;
                            }
                        }
                        if (bumpTarget != null && bumpTarget.getStatus() == Status.PENDING) {
                            bumpTarget.cancel(clock.now(), "bumped");
                            log.write("CANCELLED #" + bumpTarget.getId() + ": bumped for emergency");
                        } else {
                            throw new IllegalStateException("Emergency booking cannot bump a CONFIRMED appointment.");
                        }
                    } else {
                        throw new IllegalStateException(
                                "Staff #" + staffMember.getId() + " is already booked at hour " + hour + ".");
                    }
                }

                if (this.twist == 2 && hasBufferConflict(staffMember, hour)) {
                    throw new IllegalStateException("Booking violates required " + staffMember.bufferHours()
                            + "-hour buffer for " + staffMember.getName() + ".");
                }

                double fee = calculatePrice(patient, staffMember);
                Appointment appt = new Appointment(nextAppointmentId++, patient, staffMember, hour, fee);
                appointments.put(appt.getId(), appt);

                log.write(String.format(Locale.US, "BOOKED #%d: %s with %s at hour %d, fee %.2f, PENDING",
                        appt.getId(), patient.getName(), staffMember.getName(), hour, appt.getFee()));
                return appt;
            } catch (Exception e) {
                log.write("FAILED booking: " + e.getMessage());
                throw e;
            }
        }

        public void confirm(int appointmentId) {
            try {
                Appointment appt = appointments.get(appointmentId);
                if (appt == null) {
                    throw new IllegalArgumentException("Appointment #" + appointmentId + " does not exist.");
                }
                appt.confirm();
                log.write("CONFIRMED #" + appointmentId);
            } catch (Exception e) {
                log.write("FAILED confirm #" + appointmentId + ": " + e.getMessage());
                throw e;
            }
        }

        public void cancel(int appointmentId, String reason) {
            try {
                Appointment appt = appointments.get(appointmentId);
                if (appt == null) {
                    throw new IllegalArgumentException("Appointment #" + appointmentId + " does not exist.");
                }
                appt.cancel(clock.now(), reason);
                log.write("CANCELLED #" + appointmentId + ": " + reason);

                if (this.twist == 0) {
                    offerWaitingPatient(appt.getStaff(), appt.getStartHour());
                }
            } catch (Exception e) {
                log.write("FAILED cancel #" + appointmentId + ": " + e.getMessage());
                throw e;
            }
        }

        public void cancel(int appointmentId) {
            cancel(appointmentId, "patient request");
        }

        public void joinWaitingList(Patient patient, Staff staffMember) {
            try {
                if (this.twist != 0) {
                    throw new IllegalStateException("Waiting lists are only active for Twist 0.");
                }
                if (!patients.containsKey(patient.getId()) || !staff.containsKey(staffMember.getId())) {
                    throw new IllegalArgumentException("Patient and staff must both be registered first.");
                }
                waitingList.computeIfAbsent(staffMember.getId(), k -> new ArrayDeque<>()).addLast(patient);
                log.write("WAITLIST: Patient #" + patient.getId() + " joined waiting list for " + staffMember.getName()
                        + " (#" + staffMember.getId() + ")");
            } catch (Exception e) {
                log.write("FAILED waitlist: " + e.getMessage());
                throw e;
            }
        }

        private Appointment offerWaitingPatient(Staff staffMember, int hour) {
            Deque<Patient> queue = waitingList.get(staffMember.getId());
            if (queue == null || queue.isEmpty()) {
                log.write("WAITLIST: No waiting patient for " + staffMember.getName() + " at hour " + hour);
                return null;
            }
            int size = queue.size();
            for (int i = 0; i < size; i++) {
                Patient candidate = queue.pollFirst();
                if (!hasDirectConflict(candidate.getId(), hour, false)) {
                    double fee = calculatePrice(candidate, staffMember);
                    Appointment appt = new Appointment(nextAppointmentId++, candidate, staffMember, hour, fee);
                    appointments.put(appt.getId(), appt);
                    log.write("WAITLIST OFFER: new PENDING appointment #" + appt.getId() +
                            " for patient #" + candidate.getId() + " with " + staffMember.getName() + " at hour "
                            + hour);
                    return appt;
                }
                queue.addLast(candidate); // Cycle back if conflict
            }
            log.write("WAITLIST: No conflict-free patient found for " + staffMember.getName() + " at hour " + hour);
            return null;
        }

        public void printStaffFees() {
            for (Staff member : staff.values()) {
                System.out.println(member.role() + ": $" + member.fee());
            }
        }
    }

    public static void main(String[] args) {
        System.out.println("======================================================================");
        System.out.println("CLINIC APPOINTMENT SYSTEM DEMO (Java 17, P = " + P + ", Twist = " + (P % 4) + ")");
        System.out.println("======================================================================");

        FakeClock clock = new FakeClock(10);

        try (AppointmentLog log = new AppointmentLog("appointment.log").open()) {
            Clinic clinic = new Clinic(clock, log, P % 4);

            System.out.println("\n--- 1. Registering Staff and Patients ---");
            Patient p1 = new Patient("Tariro Moyo", 1, "student");
            Patient p2 = new Patient("Kundai Sithole", 2, "visitor");
            Patient p3 = new Patient("Farai Shumba", 3, "staff-member");

            Doctor doc = new Doctor("Dr. Chipo Ndlovu", 101);
            Nurse nurse = new Nurse("Nurse Tendai Dube", 102);
            Pharmacist pharm = new Pharmacist("Pharm. Rutendo Gumbo", 103);

            clinic.registerPatient(p1);
            clinic.registerPatient(p2);
            clinic.registerPatient(p3);

            clinic.registerStaff(doc);
            clinic.registerStaff(nurse);
            clinic.registerStaff(pharm);

            System.out.println("\n--- 2. Staff Roles and Fees (Polymorphic Loop) ---");
            clinic.printStaffFees();

            System.out.println("\n--- 3. Standard Booking and Confirmation ---");
            Appointment appt1 = clinic.book(p1, doc, 20);
            clinic.confirm(appt1.getId());

            System.out.println("\n--- 4. Deliberate Failure Demo (Too Late to Cancel) ---");
            clock.set(19); 
            try {
                System.out.println("Attempting to cancel #" + appt1.getId() + " at hour " + clock.now() + " (start is "
                        + appt1.getStartHour() + ")...");
                clinic.cancel(appt1.getId());
            } catch (IllegalStateException e) {
                System.out.println("Caught expected error: " + e.getMessage());
            }

            System.out.println("\n--- 5. Interface Restructuring & Single Constructor Call ---");
            int countBefore = Person.constructorCount;
            MedicalLecturer medLec = new MedicalLecturer("Dr. Blessing Mutasa", 201, "HCS301-Clinical");
            int countAfter = Person.constructorCount;
            int runs = countAfter - countBefore;

            System.out.println("Created: " + medLec.getName());
            System.out.println("Role: " + medLec.role());
            System.out.println("Fee: $" + medLec.fee());
            System.out.println("Module: " + medLec.getModuleName());
            System.out.println("Person constructor calls: " + runs + " (Expected: 1)");
            if (runs != 1) {
                throw new AssertionError("Person constructor executed more than once!");
            }

            int activeTwist = clinic.getTwist();
            System.out.println("\n--- 6. Active Twist Demonstration (Twist " + activeTwist + ") ---");

            if (activeTwist == 0) {
                System.out.println("Demonstrating Twist 0 (Waiting List):");
                clinic.joinWaitingList(p2, doc);
                clock.set(12);
                Appointment tempAppt = clinic.book(p3, doc, 25);
                System.out.println("Cancelling appointment to trigger automatic waiting list offer...");
                clinic.cancel(tempAppt.getId(), "slot released");
            } else if (activeTwist == 1) {
                System.out.println("Demonstrating Twist 1 (Emergency Bumping):");
                clock.set(12);
                Appointment pendingAppt = clinic.book(p2, doc, 30);
                System.out.println("Created PENDING appointment #" + pendingAppt.getId());
                Patient emerPatient = new Patient("Emergency Case", 99, "visitor", true);
                clinic.registerPatient(emerPatient);
                System.out.println("Booking emergency patient at same hour (bumps PENDING)...");
                Appointment emerAppt = clinic.book(emerPatient, doc, 30);
                System.out.println("Emergency booking confirmed: #" + emerAppt.getId());
            } else if (activeTwist == 2) {
                System.out
                        .println("Demonstrating Twist 2 (Buffer Gaps): Doctor buffer = " + doc.bufferHours() + " hrs");
                System.out.println("Existing appointment is at hour 20.");
                System.out.println("Attempting to book Doctor at hour 21 (within buffer gap)...");
                try {
                    clinic.book(p2, doc, 21);
                } catch (IllegalStateException e) {
                    System.out.println("Caught expected buffer conflict: " + e.getMessage());
                }
                System.out.println("Attempting valid booking at hour 23 (2-hour buffer respected)...");
                Appointment validAppt = clinic.book(p2, doc, 23);
                System.out
                        .println("Successfully booked #" + validAppt.getId() + " at hour " + validAppt.getStartHour());
            } else if (activeTwist == 3) {
                System.out.println("Demonstrating Twist 3 (Polymorphic Patient Discounts):");
                Appointment studentAppt = clinic.book(p1, pharm, 40);
                Appointment visitorAppt = clinic.book(p2, pharm, 41);
                Appointment staffAppt = clinic.book(p3, pharm, 42);
                System.out.println("Pharmacist Base Fee: $" + pharm.fee());
                System.out.printf(Locale.US, "Student fee (50%% off): $%.2f%n", studentAppt.getFee());
                System.out.printf(Locale.US, "Visitor fee (0%% off):  $%.2f%n", visitorAppt.getFee());
                System.out.printf(Locale.US, "Staff fee (100%% off):  $%.2f%n", staffAppt.getFee());
            }

            System.out.println("\n--- 7. Final Appointment Snapshot ---");
            for (Appointment a : clinic.getAppointments()) {
                System.out.printf(Locale.US,
                        "ID #%d | Hour: %03d | Patient: %-18s | Staff: %-20s | Status: %-9s | Fee: $%.2f%n",
                        a.getId(), a.getStartHour(), a.getPatient().getName(),
                        a.getStaff().getName(), a.getStatus(), a.getFee());
            }

        } catch (IOException e) {
            System.err.println("Fatal logging error: " + e.getMessage());
        }

        System.out.println("\n[log] session exited cleanly. appointment.log updated.");
        System.out.println("======================================================================");
    }
}