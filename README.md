# Code Analyser

A comprehensive web application for code analysis, management, and AI-powered assistance using Google Gemini API.

## Features

- **Code Upload & Analysis**: Upload code files and get instant AI-powered analysis
- **AI Chat Assistant**: Chat with an intelligent code assistant powered by Google Gemini
- **RAG System**: Retrieval-Augmented Generation for context-aware responses
- **User Authentication**: Secure login/signup system
- **Code Management**: Store and manage code files in SQLite database
- **Real-time Analysis**: Get quality assessment, bug detection, and optimization suggestions

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite3
- **AI Integration**: Google Gemini API
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentication**: Session-based authentication

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Samviksanjee/Code-Analysier
   cd code-analyser
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Copy `env_example.txt` to `.env`
   - Update the API key and secret key in `.env`:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your browser and go to `http://localhost:5000`

## Usage

### Getting Started

1. **Sign Up**: Create a new account or login with existing credentials
2. **Upload Code**: Go to the Upload Code section and paste your code
3. **View Analysis**: Check the analysis results in your dashboard
4. **Chat with Bot**: Use the chat feature to ask questions about your code

### Features Overview

#### Code Upload & Analysis
- Upload code files with filename and language specification
- Get comprehensive AI analysis including:
  - Code quality assessment
  - Bug detection and potential issues
  - Performance optimization suggestions
  - Security considerations
  - Best practices recommendations

#### AI Chat Assistant
- Ask questions about your uploaded code
- Get help with programming concepts
- Debugging assistance
- Code optimization suggestions
- Context-aware responses using RAG system

#### Dashboard
- View all uploaded code files
- Access analysis results
- Manage your code library
- Quick access to all features

## API Integration

The application uses Google Gemini API for:
- Code analysis and quality assessment
- AI-powered chat responses
- RAG (Retrieval-Augmented Generation) system

### Getting Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add the key to your `.env` file

## Database Schema

The application uses SQLite3 with the following tables:

- **users**: User authentication and profile information
- **code_files**: Stored code files with analysis results
- **chat_history**: Chat conversation history

## Project Structure

```
code-analyser/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── env_example.txt       # Environment variables template
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── upload.html
│   ├── chat.html
│   └── analysis.html
└── static/               # Static files
    ├── style.css
    └── script.js
```

## Security Features

- Password hashing using SHA-256
- Session-based authentication
- SQL injection protection
- Input validation and sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the repository.

## Future Enhancements

- [ ] File upload support (drag & drop)
- [ ] Multiple programming language support
- [ ] Code comparison features
- [ ] Export analysis reports
- [ ] Team collaboration features
- [ ] Advanced code metrics
- [ ] Integration with version control systems
