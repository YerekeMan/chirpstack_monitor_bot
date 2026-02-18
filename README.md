# ChirpStack Monitor Bot

## Overview
ChirpStack Monitor Bot is a reliable monitoring tool that listens for ChirpStack events and provides real-time notifications and logging. This bot can be easily deployed using Docker, offering flexibility and ease of use.

## Features
- Real-time monitoring of ChirpStack events.
- Configurable alerts and notifications.
- Support for custom logging.
- Docker support for easy deployment.

## Setup Instructions
1. **Clone the Repository**  
   Clone this repository to your local machine:  
   ```bash  
   git clone https://github.com/YerekeMan/chirpstack_monitor_bot.git  
   ```  

2. **Navigate to the Directory**  
   Change into the project directory:  
   ```bash  
   cd chirpstack_monitor_bot  
   ```  

3. **Create a `.env` File**  
   Create a `.env` file in the root directory and populate with the required environment variables (see below).

4. **Run the Bot**  
   Start the bot using Docker:  
   ```bash  
   docker-compose up -d  
   ```  

## Environment Variables 
| Variable Name | Description |
|----------------|-------------|
| `CHIRPSTACK_URL` | The URL of your ChirpStack instance. |
| `NOTIFICATION_CHANNEL` | The channel used for sending notifications (e.g., email, Slack). |
| `LOG_LEVEL` | Logging level (e.g., info, debug). |

## Docker Deployment
- Ensure Docker and Docker Compose are installed on your system.
- Use the following command to build the Docker image:  
```bash  
docker-compose build  
```
- Start the deployment with:  
```bash  
docker-compose up -d  
```
- To stop the bot, use:  
```bash  
docker-compose down  
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## Contact
For further questions, please reach out to the maintainer:
- **Username:** YerekeMan

---

Enjoy using the ChirpStack Monitor Bot!  
