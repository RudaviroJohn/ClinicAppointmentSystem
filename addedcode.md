            print("\nTesting updated Nurse buffer:")

            print(f"Nurse buffer = {nurse.buffer_hours()} hours")

            nurse_appt = clinic.book(p2, nurse, hour=50)

            print("Attempting to book another nurse appointment at hour 52...")

            try:
                clinic.book(p3, nurse, hour=52)
            except ValueError as err:
                print(f"Caught expected error: {err}")

            print("Attempting a valid booking at hour 53...")

            valid_nurse_appt = clinic.book(p3, nurse, hour=53)

            print(f"Successfully booked at hour {valid_nurse_appt.start_hour}")0