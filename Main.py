from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify  # pyright: ignore[reportMissingImports]
import sqlite3
import os
import google.generativeai as genai  
from werkzeug.utils import secure_filename
import hashlib
import json
import uuid
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')
DATABASE = 'code_analyser.db'

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Code files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS code_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            content TEXT NOT NULL,
            language TEXT,
            analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Chat history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            code_context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash

def get_user_by_username(username):
    """Get user by username"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_email(email):
    """Get user by email"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(username, email, password):
    """Create a new user"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    password_hash = hash_password(password)
    cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                   (username, email, password_hash))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def save_code_file(user_id, filename, content, language=None):
    """Save uploaded code file"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO code_files (user_id, filename, content, language) VALUES (?, ?, ?, ?)',
                   (user_id, filename, content, language))
    conn.commit()
    file_id = cursor.lastrowid
    conn.close()
    return file_id

def get_user_code_files(user_id):
    """Get all code files for a user"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM code_files WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    files = cursor.fetchall()
    conn.close()
    return files

def analyze_code_with_gemini(code_content, language=None):
    """Analyze code using Gemini API with enhanced analysis"""
    try:
        prompt = f"""
        As an expert code reviewer, provide a comprehensive analysis of the following {language if language else 'code'}.
        
        Please structure your analysis as follows:
        
        ## Code Quality Assessment
        - Overall code structure and organization
        - Readability and maintainability
        - Code style and conventions
        
        ## Potential Issues & Bugs
        - Logic errors or potential runtime issues
        - Edge cases that might not be handled
        - Common pitfalls or anti-patterns
        
        ## Performance Considerations
        - Time and space complexity analysis
        - Potential bottlenecks
        - Optimization opportunities
        
        ## Security Analysis
        - Security vulnerabilities
        - Input validation issues
        - Data protection concerns
        
        ## Best Practices & Recommendations
        - Industry best practices for {language if language else 'this programming language'}
        - Code improvement suggestions
        - Refactoring opportunities
        
        ## Code Examples (if applicable)
        - Show improved versions of problematic sections
        - Provide alternative implementations
        
        Code to analyze:
        ```
        {code_content}
        ```
        
        Please provide a detailed, actionable analysis that will help the developer improve their code.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error analyzing code: {str(e)}"

def get_rag_response(user_query, user_id):
    """Generate RAG response using user's code context with enhanced retrieval"""
    try:
        # Get user's recent code files for context
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT content, filename, language, analysis FROM code_files WHERE user_id = ? ORDER BY created_at DESC LIMIT 10', (user_id,))
        code_files = cursor.fetchall()
        
        # Get recent chat history for context
        cursor.execute('SELECT user_message, bot_response FROM chat_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 3', (user_id,))
        chat_history = cursor.fetchall()
        conn.close()
        
        # Enhanced context building with semantic relevance
        context = build_semantic_context(user_query, code_files, chat_history)
        
        # Generate response with enhanced context
        prompt = f"""
        You are an expert code analysis assistant with deep knowledge of programming best practices, debugging, and software engineering. 
        
        Based on the user's code context and their question, provide a comprehensive, helpful response.
        
        CONTEXT:
        {context}
        
        USER QUESTION: {user_query}
        
        INSTRUCTIONS:
        1. If the question is about specific code, reference the relevant code snippets
        2. Provide practical, actionable advice
        3. Include code examples when helpful
        4. Mention potential issues, optimizations, or best practices
        5. Be specific and detailed in your explanations
        6. If the question is general programming, provide comprehensive guidance
        
        Please provide a detailed and helpful response:
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"

def build_semantic_context(user_query, code_files, chat_history):
    """Build semantic context based on query relevance"""
    context_parts = []
    
    # Add recent chat context
    if chat_history:
        context_parts.append("RECENT CONVERSATION CONTEXT:")
        for user_msg, bot_resp in reversed(chat_history):
            context_parts.append(f"User: {user_msg}")
            context_parts.append(f"Assistant: {bot_resp[:200]}...")
        context_parts.append("")
    
    # Analyze query to determine relevant code files
    query_lower = user_query.lower()
    relevant_files = []
    
    # Simple keyword matching for relevance
    for content, filename, language, analysis in code_files:
        relevance_score = 0
        
        # Check for language-specific queries
        if language and language.lower() in query_lower:
            relevance_score += 3
        
        # Check for filename mentions
        if filename.lower() in query_lower:
            relevance_score += 2
        
        # Check for common programming terms in content
        programming_terms = ['function', 'class', 'import', 'def', 'var', 'const', 'let', 'if', 'for', 'while', 'try', 'catch']
        for term in programming_terms:
            if term in query_lower and term in content.lower():
                relevance_score += 1
        
        if relevance_score > 0:
            relevant_files.append((relevance_score, content, filename, language, analysis))
    
    # Sort by relevance and take top files
    relevant_files.sort(key=lambda x: x[0], reverse=True)
    relevant_files = relevant_files[:3]  # Top 3 most relevant files
    
    # Add relevant code context
    if relevant_files:
        context_parts.append("RELEVANT CODE FILES:")
        for _, content, filename, language, analysis in relevant_files:
            context_parts.append(f"File: {filename} (Language: {language})")
            context_parts.append(f"Code:\n{content[:1000]}{'...' if len(content) > 1000 else ''}")
            if analysis:
                context_parts.append(f"Previous Analysis: {analysis[:500]}{'...' if len(analysis) > 500 else ''}")
            context_parts.append("")
    
    # Add general code context if no specific matches
    if not relevant_files and code_files:
        context_parts.append("USER'S RECENT CODE FILES:")
        for content, filename, language, analysis in code_files[:2]:  # Top 2 recent files
            context_parts.append(f"File: {filename} (Language: {language})")
            context_parts.append(f"Code:\n{content[:800]}{'...' if len(content) > 800 else ''}")
            context_parts.append("")
    
    return "\n".join(context_parts)

def save_chat_message(user_id, session_id, user_message, bot_response, code_context=None):
    """Save chat message to database with enhanced context tracking"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Truncate context if too long for database
    if code_context and len(code_context) > 5000:
        code_context = code_context[:5000] + "... [truncated]"
    
    cursor.execute('INSERT INTO chat_history (user_id, session_id, user_message, bot_response, code_context) VALUES (?, ?, ?, ?, ?)',
                   (user_id, session_id, user_message, bot_response, code_context))
    conn.commit()
    conn.close()

def get_chat_history(user_id, session_id):
    """Get chat history for a session"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM chat_history WHERE user_id = ? AND session_id = ? ORDER BY created_at ASC', 
                   (user_id, session_id))
    history = cursor.fetchall()
    conn.close()
    return history

# Routes
@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = get_user_by_username(username)
        if user and verify_password(password, user[3]):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        if get_user_by_username(username):
            flash('Username already exists', 'error')
            return render_template('signup.html')
        
        if get_user_by_email(email):
            flash('Email already exists', 'error')
            return render_template('signup.html')
        
        try:
            create_user(username, email, password)
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Error creating account', 'error')
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    if 'user_id' not in session:
        flash('Please login to access dashboard', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    code_files = get_user_code_files(user_id)
    return render_template('dashboard.html', code_files=code_files)

@app.route('/upload', methods=['GET', 'POST'])
def upload_code():
    """Upload code section"""
    if 'user_id' not in session:
        flash('Please login to upload code', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        code_content = request.form['code_content']
        filename = request.form['filename']
        language = request.form.get('language', 'unknown')
        
        if code_content and filename:
            user_id = session['user_id']
            file_id = save_code_file(user_id, filename, code_content, language)
            
            # Analyze code with Gemini
            analysis = analyze_code_with_gemini(code_content, language)
            
            # Update analysis in database
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('UPDATE code_files SET analysis = ? WHERE id = ?', (analysis, file_id))
            conn.commit()
            conn.close()
            
            flash('Code uploaded and analyzed successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Please provide both filename and code content', 'error')
    
    return render_template('upload.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    """Chat with code bot section"""
    if 'user_id' not in session:
        flash('Please login to access chat', 'error')
        return redirect(url_for('login'))
    
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    user_id = session['user_id']
    session_id = session['session_id']
    
    if request.method == 'POST':
        user_message = request.form['user_message']
        if user_message:
            # Generate RAG response with enhanced context
            bot_response = get_rag_response(user_message, user_id)
            
            # Get the context used for this response
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT content, filename, language FROM code_files WHERE user_id = ? ORDER BY created_at DESC LIMIT 5', (user_id,))
            code_files = cursor.fetchall()
            conn.close()
            
            # Build context summary for storage
            context_summary = f"Query: {user_message}\nRelevant files: {len(code_files)} code files analyzed"
            
            # Save to chat history with context
            save_chat_message(user_id, session_id, user_message, bot_response, context_summary)
            
            return jsonify({
                'user_message': user_message,
                'bot_response': bot_response
            })
    
    # Get chat history
    chat_history = get_chat_history(user_id, session_id)
    return render_template('chat.html', chat_history=chat_history)

@app.route('/analyze/<int:file_id>')
def analyze_code(file_id):
    """Analyze specific code file"""
    if 'user_id' not in session:
        flash('Please login to analyze code', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM code_files WHERE id = ? AND user_id = ?', (file_id, session['user_id']))
    file_data = cursor.fetchone()
    conn.close()
    
    if not file_data:
        flash('File not found', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('analysis.html', file_data=file_data)

@app.route('/delete/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    """Delete a code file"""
    if 'user_id' not in session:
        flash('Please login to delete files', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Check if file belongs to user
    cursor.execute('SELECT * FROM code_files WHERE id = ? AND user_id = ?', (file_id, session['user_id']))
    file_data = cursor.fetchone()
    
    if file_data:
        # Delete the file
        cursor.execute('DELETE FROM code_files WHERE id = ? AND user_id = ?', (file_id, session['user_id']))
        conn.commit()
        flash('File deleted successfully!', 'success')
    else:
        flash('File not found or access denied', 'error')
    
    conn.close()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
