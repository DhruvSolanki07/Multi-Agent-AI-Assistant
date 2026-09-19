# Multi-Agent AI Assistant

A sophisticated multi-agent AI assistant system designed to handle complex tasks through specialized AI agents working in coordination.

## Project Structure

- `backend/` - Python-based backend services
- `frontend/` - React/Vite-based user interface
- `data/` - Task data storage
- `.kilo/` - Kilo AI configuration files

## Backend

The backend consists of multiple AI agents that work together to process tasks:

- **Planner Agent** - Breaks down complex tasks into manageable steps
- **Searcher Agent** - Gathers information from various sources
- **Writer Agent** - Creates content based on gathered information
- **Critic Agent** - Reviews and improves the output
- **Summarizer Agent** - Condenses information into key points
- **Documenter Agent** - Creates documentation and reports

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Unix/MacOS: `source .venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to add your API keys and configuration.

6. Run the backend server:
   ```bash
   python -m app.main
   ```

## Frontend

The frontend provides an interactive web interface for users to interact with the multi-agent system.

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and visit `http://localhost:5173` (or the URL shown in the terminal)

## Features

- Multi-agent collaboration for complex task processing
- Task management and tracking
- Real-time progress updates
- File upload and processing capabilities
- Configurable agent behaviors
- Extensible architecture for adding new agents

## Technologies Used

### Backend
- Python 3.8+
- FastAPI for API endpoints
- Pydantic for data validation
- Various LLM integrations (configurable)

### Frontend
- React 18+
- Vite for fast development
- TypeScript
- Tailwind CSS for styling
- Axios for HTTP requests

## How It Works

1. User submits a task through the frontend interface
2. The Planner agent breaks down the task into subtasks
3. Specialized agents (Searcher, Writer, etc.) process each subtask
4. The Critic agent reviews and improves outputs
5. The Summarizer agent creates concise summaries
6. Results are presented to the user through the frontend

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or support, please open an issue on the GitHub repository.