import React, { useState } from 'react';

function ChatBox({ onSendMessage, messages }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() !== '') {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div style={{
      border: '1px solid #ccc',
      padding: '1rem'
    }}>
      <div style={{
        height: '200px',
        overflowY: 'auto',
        border: '1px solid #ddd',
        padding: '0.5rem',
        marginBottom: '1rem'
      }}>
        {messages.map((msg, index) => (
          <div key={index} style={{ marginBottom: '0.5rem' }}>
            <strong>{msg.sender}:</strong> {msg.text}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} style={{ display: 'flex' }}>
        <input 
          type="text" 
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          placeholder="Type your question here..." 
          style={{ flexGrow: 1, marginRight: '0.5rem' }} 
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}

export default ChatBox;
