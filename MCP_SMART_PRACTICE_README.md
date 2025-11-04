# MCP-Powered Smart Practice

## Overview

This implementation demonstrates the **Model Context Protocol (MCP)** using Gemini AI to intelligently select practice questions for students. Unlike traditional rule-based systems, Gemini dynamically decides which analysis tools to use and when, adapting to each student's unique learning needs.

## Architecture

```
Frontend (React)                 Backend (FastAPI)
     |                                  |
     v                                  v
SmartPracticePage  ------>  /api/smart-practice/next-question-mcp
                                       |
                                       v
                              GeminiMCPClient (Decision Engine)
                                       |
                                       v
                              EducationMCPServer (Tool Provider)
                                       |
                   +-------------------+-------------------+
                   |                   |                   |
            get_student_profile  search_questions  analyze_performance
                   |                   |                   |
            calculate_zpd_diff  identify_gaps  predict_success
```

## Key Components

### 1. **EducationMCPServer** (`Backend/app/services/education_mcp_server.py`)

**Purpose**: Provides tools that Gemini can use to make intelligent decisions

**Available Tools**:
- `get_student_profile` - Retrieves student's knowledge profile with skill scores
- `search_questions` - Finds questions by skill, difficulty, and topic
- `analyze_recent_performance` - Identifies patterns, streaks, and struggles
- `calculate_zpd_difficulty` - Calculates Zone of Proximal Development (optimal difficulty)
- `identify_skill_gaps` - Detects prerequisite weaknesses
- `get_skill_prerequisites` - Returns learning dependency graph
- `predict_success_probability` - Estimates likelihood of correct answer

**Current Status**: ✅ Fully implemented with mocked data

**Future Enhancement**: Replace mocked data with actual database queries

### 2. **GeminiMCPClient** (`Backend/app/services/gemini_mcp_client.py`)

**Purpose**: Uses Gemini's function calling to orchestrate tool usage

**How It Works**:
1. Receives request for next question
2. Sends context to Gemini with available tools
3. Gemini decides which tools to call and in what order
4. Executes tools and sends results back to Gemini
5. Gemini makes final decision on question selection
6. Returns question with reasoning

**Key Feature**: Automatic tool calling - Gemini loops through tool calls until it has enough information to decide

**Model**: `gemini-2.5-flash-preview-05-20`

### 3. **FastAPI Endpoint** (`Backend/app/main.py`)

**Endpoint**: `POST /api/smart-practice/next-question-mcp`

**Request Body**:
```json
{
  "last_question_id": 101,
  "correct": true,
  "time_spent": 45,
  "session_id": "session_12345"
}
```

**Response**:
```json
{
  "status": "success",
  "question": {
    "id": 102,
    "question_text": "Find the roots of 2x² - 7x + 3 = 0",
    "difficulty": 0.6,
    "topic": "Quadratic Equations"
  },
  "mcp_decision": {
    "reasoning": "Student showed mastery of factoring, advancing to quadratic formula",
    "learning_objective": "Apply quadratic formula to find roots",
    "tools_used": ["get_student_profile", "analyze_recent_performance", "search_questions"],
    "difficulty_rationale": "Increased from 0.4 to 0.6 based on recent success"
  }
}
```

### 4. **SmartPracticePage** (`socratic-frontend/src/pages/SmartPracticePage.jsx`)

**Purpose**: React component that displays MCP-powered practice experience

**Features**:
- Shows which tools Gemini used (educational for demo)
- Displays Gemini's reasoning for question selection
- Highlights learning objectives
- Tracks session progress

**Route**: `/student/smart-practice/:subject/:grade`

## How to Use

### 1. **Start Backend**
```bash
cd Backend
uvicorn app.main:app --reload
```

### 2. **Start Frontend**
```bash
cd socratic-frontend
npm start
```

### 3. **Access Smart Practice**
1. Log in as a student
2. Navigate to **Dynamic Learning** page
3. Expand **Mathematics** section
4. Click on **"Smart Learning"** (marked with 🤖 MCP Powered)
5. Watch Gemini select questions intelligently!

## What Makes This "MCP"?

### Traditional Approach ❌
```python
def get_next_question(user_id):
    profile = get_profile(user_id)
    if profile.accuracy < 0.6:
        return search_questions(difficulty=0.3)
    else:
        return search_questions(difficulty=0.7)
```

### MCP Approach ✅
```python
def get_next_question(user_id):
    # Let Gemini decide which tools to call
    result = gemini_client.find_next_question(user_id, context)

    # Gemini might call:
    # - get_student_profile (to understand current state)
    # - identify_skill_gaps (to detect weaknesses)
    # - get_skill_prerequisites (to check dependencies)
    # - search_questions (to find appropriate problems)
    # - predict_success (to validate difficulty)

    # All dynamically based on the student's unique situation!
```

**Key Difference**:
- You provide tools
- Gemini provides intelligence
- No hardcoded logic - decisions adapt to context

## Example Decision Flow

**Scenario**: Student just answered 3 quadratic equations correctly

**Gemini's Process**:
1. Calls `get_student_profile(user_id=123)`
   - Sees: Quadratic equations at 65%, Linear equations at 85%
2. Calls `analyze_recent_performance(user_id=123, n_recent=3)`
   - Sees: 3/3 correct, all factoring questions, difficulty 0.4-0.5
3. Calls `calculate_zpd_difficulty(current_score=65, accuracy=100)`
   - Returns: target_difficulty = 0.7 (increase challenge)
4. Calls `search_questions(skill="quadratic_formula", difficulty_min=0.65, difficulty_max=0.75)`
   - Returns: 3 candidate questions
5. Calls `predict_success_probability(user_id=123, question_id=102)`
   - Returns: 68% probability (good challenge level)
6. **Decision**: Question 102 - "Apply quadratic formula"
   - **Reasoning**: "Student mastered factoring, ready for formula method"

**All of this happens automatically** - you don't write the decision logic!

## Monitoring MCP in Action

Watch the backend logs when a request comes in:

```
============================================================
🚀 MCP-POWERED SMART PRACTICE REQUEST
============================================================
👤 User ID: 123
📋 Context: {
  "last_question_id": 101,
  "correct": true
}

🧠 Asking Gemini to find optimal next question...

🔧 Gemini calling tool: get_student_profile
   Arguments: {"user_id": 123}
   ✅ Tool result: {...}

🔧 Gemini calling tool: analyze_recent_performance
   Arguments: {"user_id": 123, "n_recent": 3}
   ✅ Tool result: {...}

🔧 Gemini calling tool: calculate_zpd_difficulty
   Arguments: {"current_skill_score": 65, "recent_accuracy": 100}
   ✅ Tool result: {...}

🔧 Gemini calling tool: search_questions
   Arguments: {"skill": "quadratic_formula", "difficulty_min": 0.65}
   ✅ Tool result: {...}

✅ Gemini's decision:
{
  "question_id": 102,
  "reasoning": "Student showed mastery...",
  "tools_used": ["get_student_profile", "analyze_recent_performance", ...]
}

📖 Returning question: Find the roots of 2x² - 7x + 3 = 0
============================================================
```

## Next Steps

### Phase 1: Replace Mocked Data ✅ Complete
All MCP infrastructure is in place with mocked responses

### Phase 2: Connect to Real Database 🔄 Next
Replace mocked tool implementations in `EducationMCPServer` with actual database queries:
- Connect `get_student_profile` to real StudentUser.knowledge_profile
- Connect `search_questions` to NcertExercises/PYQs tables
- Connect `analyze_recent_performance` to GradingSession table

### Phase 3: Add More Tools 📋 Future
Potential additional tools:
- `get_learning_resources` - Find videos, articles for struggling skills
- `generate_hint` - Create contextual hints based on common mistakes
- `predict_time_to_mastery` - Estimate study time needed
- `recommend_study_path` - Multi-day learning trajectory

### Phase 4: Multi-Model Support 🌐 Future
The MCP server is model-agnostic. You could swap Gemini for:
- Claude (Anthropic)
- GPT-4 (OpenAI)
- Llama 3 (Open-source)
- Custom fine-tuned model

## Technical Notes

### Gemini Function Calling
Gemini's function calling uses a specific format:
```python
genai.GenerativeModel(
    'gemini-2.5-flash-preview-05-20',
    tools=[tool_declarations],
    system_instruction="..."
)
```

Tool declarations follow this schema:
```python
genai.protos.FunctionDeclaration(
    name="tool_name",
    description="what it does",
    parameters=genai.protos.Schema(...)
)
```

### Async Support
All tool calls are async-compatible:
```python
result = await gemini_client.find_next_question(user_id, context)
```

### Error Handling
Fallback to default question if Gemini fails:
```python
if "error" in result:
    question_id = result.get("fallback_question_id", 101)
```

## Cost Considerations

**Gemini 2.5 Flash Pricing** (as of 2024):
- Input: ~$0.075 per 1M tokens
- Output: ~$0.30 per 1M tokens

**Typical Request**:
- Input: ~1,500 tokens (prompt + tool results)
- Output: ~500 tokens (reasoning + decision)
- Cost: **~$0.0002 per question selection**

**For 1,000 students doing 10 questions each**:
- Total requests: 10,000
- Total cost: **~$2.00**

Very affordable for the intelligence gained!

## Questions?

This implementation demonstrates MCP at its core: **tools are dumb, models are smart**. You provide capabilities, Gemini provides reasoning.

The same MCP server could power:
- Adaptive testing systems
- Personalized tutoring
- Curriculum planning
- Student intervention alerts

All by changing the prompt, not the tools!
