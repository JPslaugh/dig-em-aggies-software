// Base - Core polymorphic interfaces
#ifndef BASE_HPP
#define BASE_HPP

#include <string>
#include <memory>
#include <vector>
#include <chrono>

// Abstract base class for all system components
class ISystemComponent {
public:
    virtual ~ISystemComponent() = default;
    virtual bool initialize() = 0;
    virtual bool update() = 0;
    virtual bool shutdown() = 0;
    virtual std::string getStatus() const = 0;
    virtual std::string getComponentName() const = 0;
};

// Abstract base for all sensors
class ISensor : public ISystemComponent {
public:
    virtual ~ISensor() = default;
    virtual double readValue() = 0;
    virtual bool calibrate() = 0;
    virtual bool isHealthy() const = 0;
    virtual std::string getUnits() const = 0;
};

// Abstract base for all actuators
class IActuator : public ISystemComponent {
public:
    virtual ~IActuator() = default;
    virtual bool setCommand(double value) = 0;
    virtual double getCommand() const = 0;
    virtual double getFeedback() const = 0;
    virtual bool hasInterlock() const = 0;
};

// Abstract base for communication interfaces
class ICommunicationInterface : public ISystemComponent {
public:
    virtual ~ICommunicationInterface() = default;
    virtual bool send(const std::vector<uint8_t>& data) = 0;
    virtual std::vector<uint8_t> receive() = 0;
    virtual bool isConnected() const = 0;
};

#endif

