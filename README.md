# Nibblix - Discord Task & Meeting Management Bot

A powerful Discord bot for managing tasks and meetings within your server. Keep track of team tasks, schedule meetings, and maintain organized communication channels.

## Features

### Task Management
- Create and track tasks with titles, descriptions, and due dates
- Assign tasks to specific team members
- Update task status (Not Started, In Progress, Under Review, Blocked, Completed)
- Create dedicated discussion threads for tasks
- Automated task board updates
- Due date tracking and overdue notifications

### Meeting Management
- Schedule meetings with titles, descriptions, and duration
- Set meeting times in Belgian timezone
- Assign participants
- RSVP functionality (Going, Maybe, Not Going)
- Automated reminders 30 minutes before meetings
- Track attendance in voice channels
- Meeting dashboard with real-time updates

### General Features
- Dedicated channels for task board and meeting dashboard
- Role-based permissions
- Admin commands for server management
- Ephemeral responses for clean channel maintenance
- Automatic thread cleanup

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Discord.py library
- PostgreSQL database (optional)

### Environment Setup
1. Clone the repository:
```bash
git clone [repository-url](https://github.com/rvph10/Task-Manager-Bot.git)
cd Task-Manager-Bot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Discord bot token:
```env
DISCORD_TOKEN=your_discord_bot_token
```

### Bot Setup
1. Create a new Discord application at [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a bot user and get your bot token
3. Enable necessary intents (Message Content, Server Members)
4. Invite the bot to your server with required permissions

## Commands

### Task Management
- `/setup` - Create task and meeting management channels (Admin only)
- `/create` - Create a new task with title, description, and optional due date
- `/assign` - Assign users to a task
- `/update` - Update task status
- `/thread` - Create a discussion thread for a task
- `/delete_thread` - Delete a task's discussion thread
- `/delete` - Delete a task
- `/info` - Get detailed information about a task
- `/list` - List all tasks assigned to you

### Meeting Management
- `/create_meeting` - Schedule a new meeting
- RSVP buttons on meeting announcements
- Meeting reminders and notifications

### Admin Commands
- `/reset_data` - Reset all tasks, meetings data, and delete associated channels
- `/help` - Show all available commands

## Project Structure
```
nibblix/
├── bot/
│   ├── __init__.py
│   ├── client.py
│   ├── commands.py
│   └── constant.py
├── core/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── models.py
│   └── persistence.py
├── features/
│   ├── __init__.py
│   ├── board_manager.py
│   ├── meeting_manager.py
│   └── task_manager.py
├── ui/
│   ├── __init__.py
│   ├── embeds.py
│   ├── meeting_views.py
│   ├── modals.py
│   └── views.py
├── utils/
│   └── validator.py
├── .env
├── config.py
├── bot.py
└── README.md
```

## Development

### Adding New Features
1. Create necessary models in `core/models.py`
2. Add storage functionality in `core/persistence.py`
3. Implement feature logic in `features/`
4. Add UI components in `ui/`
5. Add commands in `bot/commands.py`

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Document functions and classes
- Handle exceptions appropriately
- Use async/await for Discord API calls

## Error Handling
The bot includes comprehensive error handling:
- Invalid input validation
- Permission checks
- Discord API error handling
- Database operation error handling
- User-friendly error messages

## Data Storage
- Tasks and meetings are stored in JSON files
- Automatic data persistence
- Backup functionality (TODO)

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request