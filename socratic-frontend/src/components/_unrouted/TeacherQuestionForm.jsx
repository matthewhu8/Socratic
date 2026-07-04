//// filepath: /Users/matthewhu/Code/SocraticMonoRepo/socratic-frontend/src/components/TeacherQuestionForm.jsx
import React from 'react';

function TeacherQuestionForm({ newQuestion, setNewQuestion, onSubmit, isEditing }) {
  // Parse hidden values input into an object when it changes
  const handleHiddenValuesChange = (e) => {
    const valuesString = e.target.value;
    // Keep the raw string for display in the form
    setNewQuestion({ ...newQuestion, hiddenValuesRaw: valuesString });
    
    // Try to parse it into an object format for storage
    try {
      // Split by commas, then by equals sign
      const valuesObj = {};
      valuesString.split(',').forEach(pair => {
        const [key, value] = pair.trim().split('=');
        if (key && value) {
          // Try to convert to number if possible
          const numValue = parseFloat(value);
          valuesObj[key.trim()] = isNaN(numValue) ? value.trim() : numValue;
        }
      });
      setNewQuestion({ 
        ...newQuestion, 
        hiddenValuesRaw: valuesString,
        hiddenValues: valuesObj 
      });
    } catch (error) {
      console.error("Error parsing hidden values:", error);
    }
  };

  return (
    <form onSubmit={onSubmit} className="question-form">
      <div className="form-group">
        <label>
          Public Question (required):<br />
          <textarea
            value={newQuestion.publicQuestion || ''}
            onChange={(e) => setNewQuestion({ ...newQuestion, publicQuestion: e.target.value })}
            required
            className="form-textarea"
            placeholder="What is the sum of x and y?"
          />
        </label>
      </div>
      
      <div className="form-group">
        <label>
          Hidden Values (required):<br />
          <input
            type="text"
            value={newQuestion.hiddenValuesRaw || ''}
            onChange={handleHiddenValuesChange}
            required
            className="form-input"
            placeholder="e.g. x=3, y=10"
          />
        </label>
        <small className="form-tip">Format: var1=value1, var2=value2</small>
      </div>
      
      <div className="form-group">
        <label>
          Answer (required):<br />
          <input
            type="text"
            value={newQuestion.answer || ''}
            onChange={(e) => {
              const value = e.target.value;
              // Try to convert to number if possible
              const numValue = parseFloat(value);
              setNewQuestion({ ...newQuestion, answer: isNaN(numValue) ? value : numValue });
            }}
            required
            className="form-input"
            placeholder="e.g. 13"
          />
        </label>
      </div>
      
      <div className="form-group">
        <label>
          Formula (optional):<br />
          <input
            type="text"
            value={newQuestion.formula || ''}
            onChange={(e) => setNewQuestion({ ...newQuestion, formula: e.target.value })}
            className="form-input"
            placeholder="e.g. sum = x + y"
          />
        </label>
      </div>
      
      <div className="form-group">
        <label>
          Teacher Instructions (optional):<br />
          <textarea
            value={newQuestion.teacherInstructions || ''}
            onChange={(e) => setNewQuestion({ ...newQuestion, teacherInstructions: e.target.value })}
            className="form-textarea"
            placeholder="Guide students to discover both variables before solving..."
          />
        </label>
      </div>
      
      <div className="form-row">
        <div className="form-group form-group-half">
          <label>
            Hint Level:
            <select
              value={newQuestion.hintLevel || 'easy'}
              onChange={(e) => setNewQuestion({ ...newQuestion, hintLevel: e.target.value })}
              className="form-select"
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </label>
        </div>
        
        <div className="form-group form-group-half">
          <label>
            Subject:
            <input
              type="text"
              value={newQuestion.subject || ''}
              onChange={(e) => setNewQuestion({ ...newQuestion, subject: e.target.value })}
              className="form-input"
              placeholder="e.g. mathematics"
            />
          </label>
        </div>
      </div>
      
      <div className="form-group">
        <label>
          Topic:
          <input
            type="text"
            value={newQuestion.topic || ''}
            onChange={(e) => setNewQuestion({ ...newQuestion, topic: e.target.value })}
            className="form-input"
            placeholder="e.g. basic_arithmetic"
          />
        </label>
      </div>
      
      <button type="submit" className={`add-question-btn ${isEditing ? 'editing' : ''}`}>
        {isEditing ? 'Update Question' : 'Add Question'}
      </button>
    </form>
  );
}

export default TeacherQuestionForm;