// ControlSystem.hpp
#ifndef CONTROL_SYSTEM_HPP
#define CONTROL_SYSTEM_HPP

#include "base.hpp"
#include "sensors.hpp"
#include "actuators.hpp"
#include "comms.hpp"
#include "safety.hpp"
#include "data_logger.hpp"
#include "ecu.hpp"
#include "ecu_mangr.hpp"
#include <iostream>
#include <vector>
#include <memory>
#include <map>
#include <chrono>
#include <thread>
#include <fstream>
#include <sstream>
#include <iomanip>

class TM_ControlSystem {
private:
    // Component collections using polymorphism
    std::vector<std::shared_ptr<ISensor>> sensors_;
    std::vector<std::shared_ptr<IActuator>> actuators_;
    std::vector<std::shared_ptr<ICommunicationInterface>> commInterfaces_;
    
    std::unique_ptr<SafetyMonitor> safetyMonitor_;
    std::shared_ptr<DataLogger> logger_;
    std::unique_ptr<ECUManager> ecuManager_;
    
    bool systemRunning_;
    std::chrono::milliseconds loopPeriod_;
    std::string telemetryFilePath_;

    // Control state
    struct ControlState {
        double depthSetpoint;
        double headingSetpoint;
        bool autoDepthControl;
        bool autoHeadingControl;
    } controlState_;

public:
    TM_ControlSystem() 
        : systemRunning_(false), 
                    loopPeriod_(100),
                    telemetryFilePath_("./telemetry.json") { // 10 Hz default
        controlState_ = {0.0, 0.0, false, false};
                safetyMonitor_ = std::make_unique<SafetyMonitor>();
    }

    bool initialize() {
        std::cout << "Initializing ROV Control System...\n";

        // Create logger first
        logger_ = std::make_shared<DataLogger>("rov_log.txt");
        logger_->initialize();
        logger_->log("System initialization started");

        // Create ECU Manager
        ecuManager_ = std::make_unique<ECUManager>("TBM ROV Control System", logger_);
        logger_->log("ECU Manager created");

        // Setup all ECUs in the system
        setupECUs();
        
        // Initialize ECU Manager (this will initialize all ECUs)
        if (!ecuManager_->initialize()) {
            logger_->log("CRITICAL: ECU initialization failed");
            std::cerr << "ERROR: One or more ECUs failed to initialize!\n";
            return false;
        }
        
        logger_->log("All ECUs initialized successfully");
        
        // Print ECU table to console
        ecuManager_->printSystemStatus();

        // Initialize safety monitor
        if (!safetyMonitor_) {
            safetyMonitor_ = std::make_unique<SafetyMonitor>();
        }
        safetyMonitor_->initialize();

        // Initialize all sensors
        for (auto& sensor : sensors_) {
            if (!sensor->initialize()) {
                logger_->log("Failed to initialize: " + 
                           sensor->getComponentName());
                return false;
            }
            logger_->log("Initialized: " + sensor->getComponentName());
        }

        // Initialize all actuators
        for (auto& actuator : actuators_) {
            if (!actuator->initialize()) {
                logger_->log("Failed to initialize: " + 
                           actuator->getComponentName());
                return false;
            }
            logger_->log("Initialized: " + actuator->getComponentName());
            safetyMonitor_->addActuator(actuator);
        }

        // Initialize communication
        for (auto& comm : commInterfaces_) {
            if (!comm->initialize()) {
                logger_->log("Failed to initialize: " + 
                           comm->getComponentName());
                return false;
            }
            logger_->log("Initialized: " + comm->getComponentName());
        }

        logger_->log("System initialization complete");
        
        // Generate detailed ECU reports
        ecuManager_->generateDetailedReports("./ecu_reports/");
        logger_->log("ECU reports generated in ./ecu_reports/");
        
        return true;
    }

    void setupECUs() {
        logger_->log("Setting up ECU architecture...");

        // ===== ECU 1: Raspberry Pi Main Controller =====
        auto pi = std::make_shared<ECU>("ECU01", "Raspberry Pi 4B Main Controller", 
                                        ECUType::MAIN_CONTROLLER);
        
        pi->setLocation(ECULocation{
            "Main Electronics Enclosure",
            "Standoff Mount",
            0.0, 0.0, 0.0  // Reference position
        });
        
        pi->setCommunication(CommunicationInfo{
            "Local", "localhost", 0, 0, 10.0
        });
        
        pi->addControlledDevice(ControlledDevice{
            "System Coordinator", "Software", "N/A", 0
        });
        pi->addControlledDevice(ControlledDevice{
            "Safety Monitor", "Software", "N/A", 0
        });
        pi->addControlledDevice(ControlledDevice{
            "Data Logger", "Software", "N/A", 0
        });
        pi->addControlledDevice(ControlledDevice{
            "Control Algorithms (PID)", "Software", "N/A", 0
        });
        
        ecuManager_->addECU(pi);

        // ===== ECU 2: Teensy Sensor Node =====
        auto teensySensor = std::make_shared<ECU>("ECU02", "Teensy 4.0 Sensor Node", 
                                                   ECUType::SENSOR_NODE);
        
        teensySensor->setLocation(ECULocation{
            "Main Electronics Enclosure",
            "DIN Rail Mount",
            0.15, 0.0, 0.0
        });
        
        teensySensor->setCommunication(CommunicationInfo{
            "Serial UART", "/dev/ttyACM0", 115200, 0, 10.0
        });
        
        teensySensor->addControlledDevice(ControlledDevice{
            "Depth Pressure Sensor (MS5837)", "Sensor", "I2C", 0
        });
        teensySensor->addControlledDevice(ControlledDevice{
            "Water Temperature Sensor", "Sensor", "I2C", 1
        });
        teensySensor->addControlledDevice(ControlledDevice{
            "9-DOF IMU (BNO055)", "Sensor", "I2C", 2
        });
        teensySensor->addControlledDevice(ControlledDevice{
            "Internal Temperature Sensor", "Sensor", "Analog", 0
        });
        
        ecuManager_->addECU(teensySensor);

        // ===== ECU 3: Teensy Actuator Node =====
        auto teensyActuator = std::make_shared<ECU>("ECU03", "Teensy 4.0 Actuator Node", 
                                                     ECUType::ACTUATOR_NODE);
        
        teensyActuator->setLocation(ECULocation{
            "Main Electronics Enclosure",
            "DIN Rail Mount",
            0.30, 0.0, 0.0
        });
        
        teensyActuator->setCommunication(CommunicationInfo{
            "Serial UART", "/dev/ttyACM1", 115200, 0, 10.0
        });
        
        teensyActuator->addControlledDevice(ControlledDevice{
            "Vertical Thruster 1 (T200)", "Thruster", "PWM", 3
        });
        teensyActuator->addControlledDevice(ControlledDevice{
            "Vertical Thruster 2 (T200)", "Thruster", "PWM", 4
        });
        teensyActuator->addControlledDevice(ControlledDevice{
            "Horizontal Thruster 1 (T200)", "Thruster", "PWM", 5
        });
        teensyActuator->addControlledDevice(ControlledDevice{
            "Horizontal Thruster 2 (T200)", "Thruster", "PWM", 6
        });
        teensyActuator->addControlledDevice(ControlledDevice{
            "Gripper Valve", "Hydraulic Valve", "PWM", 7
        });
        teensyActuator->addControlledDevice(ControlledDevice{
            "Current Sensors (4x)", "Sensor", "Analog", 0
        });
        
        ecuManager_->addECU(teensyActuator);

        // ===== ECU 4: VFD Controller 1 - Cutter Head =====
        auto vfd1 = std::make_shared<ECU>("ECU04", "VFD Cutter Head Motor", 
                                          ECUType::VFD_CONTROLLER);
        
        vfd1->setLocation(ECULocation{
            "Power Distribution Panel",
            "Panel Mount",
            0.0, 0.25, 0.0
        });
        
        vfd1->setCommunication(CommunicationInfo{
            "Modbus RTU", "192.168.1.50", 9600, 1, 5.0
        });
        
        vfd1->addControlledDevice(ControlledDevice{
            "Cutter Head Motor (15kW)", "3-Phase Motor", "VFD", 0
        });
        
        ecuManager_->addECU(vfd1);

        // ===== ECU 5: VFD Controller 2 - Slurry Pump =====
        auto vfd2 = std::make_shared<ECU>("ECU05", "VFD Slurry Pump", 
                                          ECUType::VFD_CONTROLLER);
        
        vfd2->setLocation(ECULocation{
            "Power Distribution Panel",
            "Panel Mount",
            0.0, 0.50, 0.0
        });
        
        vfd2->setCommunication(CommunicationInfo{
            "Modbus RTU", "192.168.1.51", 9600, 2, 5.0
        });
        
        vfd2->addControlledDevice(ControlledDevice{
            "Slurry Pump Motor (22kW)", "3-Phase Motor", "VFD", 0
        });
        
        ecuManager_->addECU(vfd2);

        // ===== ECU 6: Hydraulic Controller 1 - Thrust System =====
        auto hydraulic1 = std::make_shared<ECU>("ECU06", "Hydraulic Controller - Thrust", 
                                                ECUType::HYDRAULIC_CONTROLLER);
        
        hydraulic1->setLocation(ECULocation{
            "Hydraulic Manifold Bay",
            "Manifold Mount",
            0.0, 0.0, 0.15
        });
        
        hydraulic1->setCommunication(CommunicationInfo{
            "Modbus RTU", "192.168.1.52", 9600, 3, 5.0
        });
        
        hydraulic1->addControlledDevice(ControlledDevice{
            "Thrust Cylinder 1", "Hydraulic Cylinder", "Proportional Valve", 1
        });
        hydraulic1->addControlledDevice(ControlledDevice{
            "Thrust Cylinder 2", "Hydraulic Cylinder", "Proportional Valve", 2
        });
        hydraulic1->addControlledDevice(ControlledDevice{
            "Hydraulic Pressure Sensor", "Sensor", "Analog 4-20mA", 1
        });
        
        ecuManager_->addECU(hydraulic1);

        // ===== ECU 7: Hydraulic Controller 2 - Steering =====
        auto hydraulic2 = std::make_shared<ECU>("ECU07", "Hydraulic Controller - Steering", 
                                                ECUType::HYDRAULIC_CONTROLLER);
        
        hydraulic2->setLocation(ECULocation{
            "Hydraulic Manifold Bay",
            "Manifold Mount",
            0.0, 0.0, 0.30
        });
        
        hydraulic2->setCommunication(CommunicationInfo{
            "Modbus RTU", "192.168.1.53", 9600, 4, 5.0
        });
        
        hydraulic2->addControlledDevice(ControlledDevice{
            "Steering Cylinder Left", "Hydraulic Cylinder", "Proportional Valve", 3
        });
        hydraulic2->addControlledDevice(ControlledDevice{
            "Steering Cylinder Right", "Hydraulic Cylinder", "Proportional Valve", 4
        });
        hydraulic2->addControlledDevice(ControlledDevice{
            "Steering Position Sensor", "Sensor", "Analog 0-10V", 2
        });
        
        ecuManager_->addECU(hydraulic2);

        logger_->log("ECU architecture setup complete - " + 
                    std::to_string(ecuManager_->getTotalECUCount()) + " ECUs configured");
    }

    void addSensor(std::shared_ptr<ISensor> sensor) {
        sensors_.push_back(sensor);
    }

    void addActuator(std::shared_ptr<IActuator> actuator) {
        actuators_.push_back(actuator);
    }

    void addCommunication(std::shared_ptr<ICommunicationInterface> comm) {
        commInterfaces_.push_back(comm);
    }

    void addSafetyLimit(const std::string& name,
                       std::function<double()> getValue,
                       double minVal, double maxVal) {
        safetyMonitor_->addLimit(name, getValue, minVal, maxVal);
    }

    void controlLoop() {
        auto lastTime = std::chrono::steady_clock::now();

        while (systemRunning_) {
            auto currentTime = std::chrono::steady_clock::now();
            auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
                currentTime - lastTime);

            if (elapsed >= loopPeriod_) {
                lastTime = currentTime;

                // 0. Update ECU health monitoring
                ecuManager_->update();
                
                // Check if all critical ECUs are online
                if (!ecuManager_->areAllECUsOnline()) {
                    logger_->log("WARNING: Not all ECUs online - " + 
                                ecuManager_->getStatus());
                    // Could implement degraded mode here
                }

                // 1. Read all sensors
                for (auto& sensor : sensors_) {
                    sensor->update();
                    double value = sensor->readValue();
                    
                    // Log periodically (every 10th iteration)
                    static int counter = 0;
                    if (++counter % 10 == 0) {
                        logger_->logComponentStatus(*sensor);
                    }
                }

                // 2. Check safety interlocks
                safetyMonitor_->update();
                if (!safetyMonitor_->isSystemSafe()) {
                    logger_->log("SAFETY FAULT: " + 
                               safetyMonitor_->getLastViolation());
                }

                // 3. Run control algorithms
                runControlAlgorithms();

                // 4. Update actuators
                for (auto& actuator : actuators_) {
                    actuator->update();
                }

                // 5. Handle communication
                for (auto& comm : commInterfaces_) {
                    comm->update();
                    processCommunication(comm);
                }
                
                // 6. Update communication timestamps for ECUs
                updateECUCommunicationStatus();

                // 7. Publish telemetry snapshot to local JSON file
                writeTelemetrySnapshot();
            }

            // Sleep briefly to avoid busy-waiting
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
    }

    void updateECUCommunicationStatus() {
        // Update timestamps when we successfully communicate with ECUs
        // This prevents watchdog timeouts
        
        // Example: Update Teensy sensor node if communication successful
        auto teensySensor = ecuManager_->getECU("ECU02");
        if (teensySensor && !commInterfaces_.empty()) {
            // If we got data from this interface, update timestamp
            teensySensor->updateCommunicationTimestamp();
        }
        
        auto teensyActuator = ecuManager_->getECU("ECU03");
        if (teensyActuator && commInterfaces_.size() > 1) {
            teensyActuator->updateCommunicationTimestamp();
        }
    }

    void runControlAlgorithms() {
        // Simple PID-style depth control example
        if (controlState_.autoDepthControl) {
            // Get depth sensor (assuming first pressure sensor)
            if (!sensors_.empty()) {
                double currentDepth = sensors_[0]->readValue();
                double error = controlState_.depthSetpoint - currentDepth;
                
                // Simple proportional control
                double thrustCommand = error * 0.5; // Kp = 0.5
                
                // Apply to vertical thrusters (example)
                if (!actuators_.empty()) {
                    actuators_[0]->setCommand(thrustCommand);
                }
            }
        }
    }

    void processCommunication(std::shared_ptr<ICommunicationInterface> comm) {
        // Receive commands from surface or Teensy
        auto data = comm->receive();
        if (!data.empty()) {
            // Parse and execute commands
            logger_->log("Received data: " + std::to_string(data.size()) + 
                        " bytes");
        }

        // Send telemetry
        std::vector<uint8_t> telemetry = buildTelemetryPacket();
        comm->send(telemetry);
    }

    std::vector<uint8_t> buildTelemetryPacket() {
        std::vector<uint8_t> packet;
        
        // Build packet with sensor data, actuator states, etc.
        // Format: [Header][Sensor1][Sensor2]...[Actuator1]...[Checksum]
        
        return packet;
    }

    std::string getIsoTimestamp() const {
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()) % 1000;

        std::stringstream ss;
        ss << std::put_time(std::gmtime(&time), "%Y-%m-%dT%H:%M:%S");
        ss << '.' << std::setfill('0') << std::setw(3) << ms.count() << "Z";
        return ss.str();
    }

    std::string jsonEscape(const std::string& input) const {
        std::string output;
        output.reserve(input.size());
        for (char c : input) {
            switch (c) {
                case '\\': output += "\\\\"; break;
                case '"': output += "\\\""; break;
                case '\n': output += "\\n"; break;
                case '\r': output += "\\r"; break;
                case '\t': output += "\\t"; break;
                default: output += c; break;
            }
        }
        return output;
    }

    void writeTelemetrySnapshot() {
        std::ofstream file(telemetryFilePath_, std::ios::trunc);
        if (!file.is_open()) {
            return;
        }

        std::stringstream ss;
        ss << "{";
        ss << "\"timestamp\":\"" << getIsoTimestamp() << "\",";

        ss << "\"system\":{";
        ss << "\"safe\":" << (safetyMonitor_ && safetyMonitor_->isSystemSafe() ? "true" : "false") << ",";
        ss << "\"violation\":\"" << jsonEscape(safetyMonitor_ ? safetyMonitor_->getLastViolation() : "") << "\"";
        ss << "},";

        ss << "\"control\":{";
        ss << "\"depthSetpoint\":" << controlState_.depthSetpoint << ",";
        ss << "\"headingSetpoint\":" << controlState_.headingSetpoint << ",";
        ss << "\"autoDepth\":" << (controlState_.autoDepthControl ? "true" : "false") << ",";
        ss << "\"autoHeading\":" << (controlState_.autoHeadingControl ? "true" : "false");
        ss << "},";

        ss << "\"sensors\":[";
        for (size_t i = 0; i < sensors_.size(); ++i) {
            const auto& sensor = sensors_[i];
            double value = sensor->readValue();
            ss << "{";
            ss << "\"name\":\"" << jsonEscape(sensor->getComponentName()) << "\",";
            ss << "\"value\":" << value << ",";
            ss << "\"units\":\"" << jsonEscape(sensor->getUnits()) << "\",";
            ss << "\"healthy\":" << (sensor->isHealthy() ? "true" : "false");

            if (auto imu = dynamic_cast<IMUSensor*>(sensor.get())) {
                auto data = imu->getData();
                ss << ",\"imu\":{";
                ss << "\"roll\":" << data.roll << ",";
                ss << "\"pitch\":" << data.pitch << ",";
                ss << "\"yaw\":" << data.yaw << ",";
                ss << "\"accelX\":" << data.accelX << ",";
                ss << "\"accelY\":" << data.accelY << ",";
                ss << "\"accelZ\":" << data.accelZ;
                ss << "}";
            }

            ss << "}";
            if (i + 1 < sensors_.size()) {
                ss << ",";
            }
        }
        ss << "],";

        ss << "\"actuators\":[";
        for (size_t i = 0; i < actuators_.size(); ++i) {
            const auto& actuator = actuators_[i];
            ss << "{";
            ss << "\"name\":\"" << jsonEscape(actuator->getComponentName()) << "\",";
            ss << "\"command\":" << actuator->getCommand() << ",";
            ss << "\"feedback\":" << actuator->getFeedback() << ",";
            ss << "\"interlock\":" << (actuator->hasInterlock() ? "true" : "false");
            ss << "}";
            if (i + 1 < actuators_.size()) {
                ss << ",";
            }
        }
        ss << "]";

        ss << "}";
        file << ss.str();
        file.close();
    }

    void start() {
        systemRunning_ = true;
        logger_->log("System started");
        controlLoop();
    }

    void stop() {
        systemRunning_ = false;
        logger_->log("System stopping");
        
        // Shutdown ECU manager first (logs all ECU shutdowns)
        if (ecuManager_) {
            ecuManager_->shutdown();
        }
        
        // Shutdown all components
        for (auto& actuator : actuators_) {
            actuator->shutdown();
        }
        for (auto& sensor : sensors_) {
            sensor->shutdown();
        }
        for (auto& comm : commInterfaces_) {
            comm->shutdown();
        }
        
        safetyMonitor_->shutdown();
        logger_->shutdown();
    }

    void printSystemStatus() {
        std::cout << "\n=== ROV System Status ===\n";
        
        // ECU Status
        std::cout << "\nECU Status:\n";
        std::cout << "  " << ecuManager_->getStatus() << "\n";
        if (!ecuManager_->areAllECUsOnline()) {
            std::cout << "  WARNING: System operating in degraded mode\n";
        }
        
        std::cout << "\nSafety: " << safetyMonitor_->getStatus() << "\n";
        
        std::cout << "\nSensors:\n";
        for (const auto& sensor : sensors_) {
            std::cout << "  " << sensor->getStatus() << "\n";
        }
        
        std::cout << "\nActuators:\n";
        for (const auto& actuator : actuators_) {
            std::cout << "  " << actuator->getStatus() << "\n";
        }
        
        std::cout << "\nCommunication:\n";
        for (const auto& comm : commInterfaces_) {
            std::cout << "  " << comm->getStatus() << "\n";
        }
        std::cout << "========================\n\n";
    }

    void printECUTable() {
        if (ecuManager_) {
            ecuManager_->printSystemStatus();
        }
    }

    void generateECUReports() {
        if (ecuManager_) {
            ecuManager_->generateDetailedReports("./ecu_reports/");
            std::cout << "ECU reports generated in ./ecu_reports/\n";
        }
    }

    // Getter for ECU manager (for advanced diagnostics)
    ECUManager* getECUManager() {
        return ecuManager_.get();
    }
};

using ROVControlSystem = TM_ControlSystem;

#endif