#include <Wire.h>
#include "MAX30105.h"  // Include the MAX30102 library
#include "heartRate.h"  // Include heart rate library for BPM calculation
#include <WiFi.h>
#include <HTTPClient.h>

MAX30105 particleSensor;
const int gsrPin = 34;  // GPIO pin for GSR sensor

// Variables for BPM calculation   
float bpm = 0;
unsigned long lastBeatTime = 0;
bool beatDetected = false;
int beatCount = 0;  // Count of beats within 1 second
unsigned long lastBpmTime = 0;  // Timer to track 1-second intervals

// Variables for SpO2 calculation
long irValues[100];  // Store recent IR values for filtering
long redValues[100];  // Store recent Red values for filtering
int irIndex = 0, redIndex = 0;  // Array indices

// Wi-Fi credentials
const char* ssid = "07-A-K-Wagle";     // Your Wi-Fi SSID
const char* password = "12345678"; // Your Wi-Fi password

// FastAPI server URL
const char* serverURL = "http://192.168.137.157:8000/data";

void setup() {
    Serial.begin(115200);  // Initialize serial communication
    while (!Serial);  // Wait for serial port to connect

    // Initialize Wi-Fi connection
    WiFi.begin(ssid, password);
    Serial.println("Connecting to WiFi...");

    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting...");
    }

    Serial.println("Connected to WiFi!");

    // Initialize the MAX30102 sensor
    if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
        Serial.println("MAX30102 not found. Check your connections.");
        while (1);  // Stay here if sensor initialization fails
    }

    // Set up the MAX30102 sensor
    particleSensor.setup();  // Configure sensor settings
    particleSensor.setPulseAmplitudeRed(0x0A);  // Set Red LED brightness
    particleSensor.setPulseAmplitudeIR(0x0A);   // Set IR LED brightness
}

void loop() {
    // Read sensor values
    long irValue = particleSensor.getIR();  // Get IR value from MAX30102
    long redValue = particleSensor.getRed();  // Get Red value from MAX30102
    int gsrValue = analogRead(gsrPin);  // Read GSR sensor value

    // Map IR value from [200, 28000] to [0, 66], with the possibility of extending to 120
    long mappedIrValue = map(irValue, 200, 28000, 0, 66);

    // If IR value exceeds 28,000, allow it to scale up to 120
    if (irValue > 28000) {
        mappedIrValue = map(irValue, 28000, 40000, 66, 120);
    }

    // Ensure mapped value doesn't exceed 120
    mappedIrValue = constrain(mappedIrValue, 0, 120);

    // Directly assign the mapped IR value as BPM
    bpm = mappedIrValue;

    // Print BPM (which is now the mapped IR value)
    Serial.print("BPM (Mapped IR Value): ");
    Serial.println(bpm);

    // Store the IR and Red values for SpO2 calculation
    irValues[irIndex] = irValue;
    redValues[redIndex] = redValue;
    irIndex = (irIndex + 1) % 100;  // Update indices cyclically
    redIndex = (redIndex + 1) % 100;

    // Calculate SpO2 based on the IR value
    float spo2 = calculateSpO2(irValue);

    // Print the SpO2 and GSR values to the serial monitor
    Serial.print("SpO2: ");
    Serial.print(spo2);
    Serial.print("%, GSR: ");
    Serial.println(gsrValue);

    // Send BPM and GSR data to the server
    if (WiFi.status() == WL_CONNECTED) {  // Check if Wi-Fi is connected
        HTTPClient http;
        http.begin(serverURL);  // Specify the server's URL

        // Prepare the JSON payload
        String payload = "{";
        payload += "\"bpm\": " + String(bpm) + ",";
        payload += "\"gsr\": " + String(gsrValue);
        payload += "}";

        // Send HTTP POST request
        http.addHeader("Content-Type", "application/json");
        int httpResponseCode = http.POST(payload);

        if (httpResponseCode > 0) {
            Serial.print("POST Request Sent, Response Code: ");
            Serial.println(httpResponseCode);
        } else {
            Serial.print("Error Sending POST Request: ");
            Serial.println(http.errorToString(httpResponseCode).c_str());
        }

        http.end();  // Close the connection
    }

    delay(100);  // Adjust the delay as needed (sampling rate of 10 Hz)
}

// Function to calculate SpO2 based on IR value
float calculateSpO2(long irValue) {
    if (irValue <= 200) {
        return 0;  // If IR value is 200 or less, SpO2 is 0
    } else if (irValue >= 28000) {
        return 95;  // Max SpO2 capped at 95 when IR is 28,000
    } else {
        // Scale SpO2 from 0 to 99 based on IR values between 200 and 28,000
        float spo2 = map(irValue, 200, 28000, 0, 99);  // Scale the output to range [0, 99]
        return constrain(spo2, 0, 99);  // Ensure SpO2 does not exceed 99
    }
}