// main
#include "controlSystem.hpp"
#include <iostream>
#include <signal.h>

ROVControlSystem* g_system = nullptr;

void signalHandler(int signum) {
    std::cout << "\nShutdown signal received...\n";
    if (g_system) {
        g_system->stop();
    }
    exit(signum);
}

int main() {
    // Register signal handler for graceful shutdown
    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);

    try {
        // Create control system
        ROVControlSystem system;
        g_system = &system;

        // Add sensors
        auto pressureSensor1 = std::make_shared<PressureSensor>("DepthSensor");
        auto tempSensor1 = std::make_shared<TemperatureSensor>("WaterTemp");
        auto imu = std::make_shared<IMUSensor>("IMU");
        
        system.addSensor(pressureSensor1);
        system.addSensor(tempSensor1);
        system.addSensor(imu);

        // Add actuators
        auto thruster1 = std::make_shared<ThrusterMotor>("VerticalThruster1");
        auto thruster2 = std::make_shared<ThrusterMotor>("HorizontalThruster1");
        auto valve1 = std::make_shared<HydraulicValve>("GripperValve");
        
        system.addActuator(thruster1);
        system.addActuator(thruster2);
        system.addActuator(valve1);

        // Add communication interfaces
        auto teensySerial1 = std::make_shared<SerialInterface>("/dev/ttyACM0", 115200);
        auto teensySerial2 = std::make_shared<SerialInterface>("/dev/ttyACM1", 115200);
        auto telemetry = std::make_shared<TelemetryUplink>("192.168.1.100", 5000);
        auto modbus = std::make_shared<ModbusInterface>("192.168.1.50");
        
        system.addCommunication(teensySerial1);
        system.addCommunication(teensySerial2);
        system.addCommunication(telemetry);
        system.addCommunication(modbus);

        // Configure safety limits
        system.addSafetyLimit("MaxDepth", 
                             [&]() { return pressureSensor1->readValue(); },
                             0.0, 100.0); // 0-100 PSI

        system.addSafetyLimit("MaxTemp",
                             [&]() { return tempSensor1->readValue(); },
                             -5.0, 50.0); // -5 to 50°C

        // Initialize and start
        if (!system.initialize()) {
            std::cerr << "Failed to initialize system!\n";
            return 1;
        }

        system.printSystemStatus();
        
        std::cout << "Starting ROV control system...\n";
        std::cout << "Press Ctrl+C to stop.\n";
        
        system.start();

    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}