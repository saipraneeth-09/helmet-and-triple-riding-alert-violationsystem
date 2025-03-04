import cv2
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import numpy as np
from ultralytics import YOLO

# Twilio Configuration
class TwilioNotifier:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'xxxxxxxxxxxxxxxxxxxxxxxx')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN', 'xxxxxxxxxxxxxxxxxxxxx')
        self.from_number = os.getenv('TWILIO_FROM_NUMBER', 'xxxxxxxxxxxxx')
        self.to_number = os.getenv('TWILIO_TO_NUMBER', 'xxxxxxxxxxxxx')
        
        try:
            self.client = Client(self.account_sid, self.auth_token)
            self.client.api.accounts(self.account_sid).fetch()
            print("Twilio client initialized successfully.")
        except TwilioRestException as e:
            print(f"Twilio authentication failed: {str(e)}")
            self.client = None
        except Exception as e:
            print(f"Failed to initialize Twilio client: {str(e)}")
            self.client = None

    def send_alert(self, message):
        if not self.client:
            print("Twilio client not initialized. Cannot send message.")
            return
        
        try:
            message = self.client.messages.create(
                from_=self.from_number,
                to=self.to_number,
                body=message
            )
            print(f"Alert sent successfully: {message.sid}")
        except TwilioRestException as e:
            print(f"Failed to send Twilio message: {str(e)}")
        except Exception as e:
            print(f"Unexpected error sending message: {str(e)}")

# Initialize Twilio notifier
twilio_notifier = TwilioNotifier()

# Load YOLOv8 model using ultralytics
model = YOLO("yolov8n.pt")  # You can use other versions like yolov8s.pt, yolov8m.pt, etc.

# YOLO frame processing with YOLOv8
def process_frame_yolo(frame):
    try:
        # Perform detection
        results = model(frame)  # Perform inference on the frame

        # Extract the detected boxes and labels
        persons_detected = 0
        helmets_detected = 0

        for result in results[0].boxes:  # Results in xyxy format [xmin, ymin, xmax, ymax, confidence, class]
            xmin, ymin, xmax, ymax = result.xyxy[0].tolist()  # xyxy format
            confidence = result.conf[0].item()  # Confidence score
            class_id = int(result.cls[0].item())  # Class ID
            label = model.names[class_id]  # Label for the detected object
            
            if confidence > 0.5:  # Confidence threshold
                if label == "person":
                    persons_detected += 1
                    # Draw bounding box for detected persons
                    cv2.rectangle(frame, (int(xmin), int(ymin)), (int(xmax), int(ymax)), (255, 0, 0), 2)
                    cv2.putText(frame, label, (int(xmin), int(ymin) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                elif label == "helmet":  # Replace with custom helmet class if trained on a specific model
                    helmets_detected += 1
                    # Draw bounding box for detected helmets
                    cv2.rectangle(frame, (int(xmin), int(ymin)), (int(xmax), int(ymax)), (0, 255, 0), 2)
                    cv2.putText(frame, label, (int(xmin), int(ymin) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Add alerts based on detections
        if persons_detected > 2:
            # Show warning on the frame for triple riding
            cv2.putText(frame, "Warning: Triple riding detected", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            twilio_notifier.send_alert("Alert: Triple riding detected! Please ensure safety.")

        if helmets_detected > 0:
            # Helmet detected message
            cv2.putText(frame, "Helmet detected", 
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            # Show warning on the frame for no helmets detected
            cv2.putText(frame, "Warning: No helmet detected", 
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            twilio_notifier.send_alert("Alert: No helmet detected! Please wear a helmet.")

        return frame

    except Exception as e:
        print(f"Error processing frame: {str(e)}")
        return frame

# Detect violations using camera and optionally record video
def detect_violations(record_video=False):
    # Use camera as the video source (0 is the default camera)
    cap = cv2.VideoCapture(0)  # 0 is the default camera, change if you have another camera device

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Set up the video writer if recording
    if record_video:
        fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec for video writing
        out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))  # Output video file

    print("Press 'q' to exit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Unable to capture frame from camera.")
            break

        # Process the frame and detect violations
        processed_frame = process_frame_yolo(frame)
        
        # Display the processed frame with bounding boxes and alerts
        cv2.imshow("Helmet and Triple Ride Detection", processed_frame)

        if record_video:
            # Write the processed frame to the video file
            out.write(processed_frame)

        # Exit if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting...")
            break

    # Release the video capture and writer objects
    cap.release()
    if record_video:
        out.release()
    cv2.destroyAllWindows()

# Main function with menu options
def main():
    while True:
        print("\nSelect an option:")
        print("1. Start video detection without recording")
        print("2. Start video detection with recording")
        print("3. Exit")

        choice = input("Enter choice (1/2/3): ").strip()

        if choice == '1':
            detect_violations(record_video=False)
        elif choice == '2':
            detect_violations(record_video=True)
        elif choice == '3':
            print("Exiting program...")
            break
        else:
            print("Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    main()
