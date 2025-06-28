import React from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { TbMathFunction, TbFlask } from 'react-icons/tb';
import { IoFlashOutline } from 'react-icons/io5';
import { FaHeart } from 'react-icons/fa';
import { TbBook } from 'react-icons/tb';
import '../styles/SubjectPage.css';

// Import topic data from existing subject pages
const topicsBySubjectAndGrade = {
  mathematics: {
    9: [
      {
        title: 'Linear Equations',
        description: 'Solving equations with one variable.',
        path: 'linear-equations',
      },
      {
        title: 'Quadratic Functions',
        description: 'Understanding parabolas and quadratic equations.',
        path: 'quadratic-functions',
      },
      {
        title: 'Basic Geometry',
        description: 'Properties of shapes and angles.',
        path: 'basic-geometry',
      },
    ],
    10: [
      {
        title: 'Real Numbers',
        description: 'Fundamental concepts of real numbers.',
        path: 'real-numbers',
      },
      {
        title: 'Polynomials',
        description: 'Properties of polynomials and their roots.',
        path: 'polynomials',
      },
      {
        title: 'Pair of Linear Equations in Two Variables',
        description: 'Solving pair of linear equations in two variables.',
        path: 'pair-of-linear-equations-in-two-variables',
      },
    ],
    11: [
      {
        title: 'Advanced Trigonometry',
        description: 'Trigonometric identities and equations.',
        path: 'advanced-trigonometry',
      },
      {
        title: 'Logarithmic Functions',
        description: 'Properties and applications of logarithms.',
        path: 'logarithmic-functions',
      },
      {
        title: 'Sequences and Series',
        description: 'Arithmetic and geometric progressions.',
        path: 'sequences-and-series',
      },
    ],
    12: [
      {
        title: 'Calculus - Limits',
        description: 'Introduction to limits and continuity.',
        path: 'calculus-limits',
      },
      {
        title: 'Calculus - Derivatives',
        description: 'Differentiation and its applications.',
        path: 'calculus-derivatives',
      },
      {
        title: 'Calculus - Integrals',
        description: 'Integration and area under curves.',
        path: 'calculus-integrals',
      },
    ],
  },
  physics: {
    9: [
      {
        title: 'Motion and Forces',
        description: 'Basic concepts of motion and Newton\'s laws.',
        path: 'motion-and-forces',
      },
      {
        title: 'Energy and Work',
        description: 'Understanding kinetic and potential energy.',
        path: 'energy-and-work',
      },
      {
        title: 'Simple Machines',
        description: 'Levers, pulleys, and mechanical advantage.',
        path: 'simple-machines',
      },
    ],
    10: [
      {
        title: 'Waves and Sound',
        description: 'Properties of waves and sound phenomena.',
        path: 'waves-and-sound',
      },
      {
        title: 'Light and Optics',
        description: 'Reflection, refraction, and lenses.',
        path: 'light-and-optics',
      },
      {
        title: 'Heat and Temperature',
        description: 'Thermal energy and heat transfer.',
        path: 'heat-and-temperature',
      },
    ],
    11: [
      {
        title: 'Electricity Basics',
        description: 'Current, voltage, and resistance.',
        path: 'electricity-basics',
      },
      {
        title: 'Magnetism',
        description: 'Magnetic fields and electromagnetic induction.',
        path: 'magnetism',
      },
      {
        title: 'Mechanics',
        description: 'Advanced motion and gravitation.',
        path: 'mechanics',
      },
    ],
    12: [
      {
        title: 'Electromagnetism',
        description: 'Electric and magnetic fields, electromagnetic waves.',
        path: 'electromagnetism',
      },
      {
        title: 'Modern Physics',
        description: 'Quantum mechanics and relativity basics.',
        path: 'modern-physics',
      },
      {
        title: 'Nuclear Physics',
        description: 'Atomic structure and radioactivity.',
        path: 'nuclear-physics',
      },
    ],
  },
  chemistry: {
    9: [
      {
        title: 'Atomic Structure',
        description: 'Basic structure of atoms and periodic table.',
        path: 'atomic-structure',
      },
      {
        title: 'Chemical Bonding',
        description: 'Ionic and covalent bonds.',
        path: 'chemical-bonding',
      },
      {
        title: 'Chemical Reactions',
        description: 'Types of chemical reactions and balancing equations.',
        path: 'chemical-reactions',
      },
    ],
    10: [
      {
        title: 'States of Matter',
        description: 'Solids, liquids, gases, and phase changes.',
        path: 'states-of-matter',
      },
      {
        title: 'Solutions and Mixtures',
        description: 'Concentration, solubility, and separation techniques.',
        path: 'solutions-and-mixtures',
      },
      {
        title: 'Chemical Formulas',
        description: 'Writing and interpreting chemical formulas.',
        path: 'chemical-formulas',
      },
    ],
    11: [
      {
        title: 'Acids and Bases',
        description: 'Properties, reactions, and pH scale.',
        path: 'acids-and-bases',
      },
      {
        title: 'Redox Reactions',
        description: 'Oxidation and reduction processes.',
        path: 'redox-reactions',
      },
      {
        title: 'Thermochemistry',
        description: 'Energy changes in chemical reactions.',
        path: 'thermochemistry',
      },
    ],
    12: [
      {
        title: 'Organic Chemistry',
        description: 'Basic principles and reactions of organic compounds.',
        path: 'organic-chemistry',
      },
      {
        title: 'Chemical Equilibrium',
        description: 'Dynamic equilibrium and Le Chatelier\'s principle.',
        path: 'chemical-equilibrium',
      },
      {
        title: 'Electrochemistry',
        description: 'Galvanic cells and electrolysis.',
        path: 'electrochemistry',
      },
    ],
  },
  biology: {
    9: [
      {
        title: 'Cell Structure',
        description: 'Basic structure and function of plant and animal cells.',
        path: 'cell-structure',
      },
      {
        title: 'Classification of Living Things',
        description: 'Five kingdom classification system.',
        path: 'classification',
      },
      {
        title: 'Basic Ecology',
        description: 'Ecosystems, food chains, and environmental factors.',
        path: 'basic-ecology',
      },
    ],
    10: [
      {
        title: 'Photosynthesis',
        description: 'Process of photosynthesis and its importance.',
        path: 'photosynthesis',
      },
      {
        title: 'Respiration',
        description: 'Cellular respiration and energy production.',
        path: 'respiration',
      },
      {
        title: 'Human Body Systems',
        description: 'Overview of major body systems.',
        path: 'human-body-systems',
      },
    ],
    11: [
      {
        title: 'Cell Biology',
        description: 'Advanced cell structure and function.',
        path: 'cell-biology',
      },
      {
        title: 'Genetics Basics',
        description: 'DNA, genes, and basic inheritance patterns.',
        path: 'genetics-basics',
      },
      {
        title: 'Evolution',
        description: 'Theory of evolution and natural selection.',
        path: 'evolution',
      },
    ],
    12: [
      {
        title: 'Advanced Genetics',
        description: 'Molecular genetics and genetic engineering.',
        path: 'advanced-genetics',
      },
      {
        title: 'Biotechnology',
        description: 'Applications of biology in technology.',
        path: 'biotechnology',
      },
      {
        title: 'Human Physiology',
        description: 'Detailed study of human body functions.',
        path: 'human-physiology',
      },
    ],
  },
  english: {
    9: [
      {
        title: 'Grammar Fundamentals',
        description: 'Parts of speech, sentence structure, and punctuation.',
        path: 'grammar-fundamentals',
      },
      {
        title: 'Reading Comprehension',
        description: 'Understanding and analyzing texts.',
        path: 'reading-comprehension',
      },
      {
        title: 'Creative Writing',
        description: 'Introduction to narrative and descriptive writing.',
        path: 'creative-writing',
      },
    ],
    10: [
      {
        title: 'Poetry Analysis',
        description: 'Understanding poetic devices and themes.',
        path: 'poetry-analysis',
      },
      {
        title: 'Essay Writing',
        description: 'Persuasive and argumentative essays.',
        path: 'essay-writing',
      },
      {
        title: 'Literature Study',
        description: 'Analyzing novels and short stories.',
        path: 'literature-study',
      },
    ],
    11: [
      {
        title: 'Advanced Grammar',
        description: 'Complex sentence structures and advanced punctuation.',
        path: 'advanced-grammar',
      },
      {
        title: 'Research Skills',
        description: 'Finding and citing reliable sources.',
        path: 'research-skills',
      },
      {
        title: 'Shakespeare Studies',
        description: 'Understanding Shakespearean language and themes.',
        path: 'shakespeare-studies',
      },
    ],
    12: [
      {
        title: 'Literary Analysis',
        description: 'Advanced techniques for analyzing literature.',
        path: 'literary-analysis',
      },
      {
        title: 'Academic Writing',
        description: 'Research papers and formal writing styles.',
        path: 'academic-writing',
      },
      {
        title: 'Public Speaking',
        description: 'Presentation skills and oral communication.',
        path: 'public-speaking',
      },
    ],
  },
};

// Helper to format text
const formatBreadcrumb = (str) => {
  if (!str) return '';
  return str
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// Helper to get practice mode display name
const getPracticeModeDisplayName = (practiceMode) => {
  const modeMap = {
    'ncert-examples': 'NCERT Examples',
    'ncert-exercises': 'NCERT Exercises',
    'previous-year-questions': 'Previous Year Questions',
    'smart-practice': 'Smart Practice',
  };
  return modeMap[practiceMode] || practiceMode;
};

// Helper to get subject icon and color
const getSubjectConfig = (subject) => {
  const config = {
    mathematics: {
      icon: <TbMathFunction />,
      color: '#4285f4',
      bgColor: '#e8f0fe'
    },
    physics: {
      icon: <IoFlashOutline />,
      color: '#9c27b0',
      bgColor: '#f3e5f5'
    },
    chemistry: {
      icon: <TbFlask />,
      color: '#4caf50',
      bgColor: '#e8f5e9'
    },
    biology: {
      icon: <FaHeart />,
      color: '#f44336',
      bgColor: '#ffebee'
    },
    english: {
      icon: <TbBook />,
      color: '#673ab7',
      bgColor: '#f3e5f5'
    }
  };
  return config[subject] || { icon: <TbBook />, color: '#666', bgColor: '#f5f5f5' };
};

function SubtopicSelectionPage() {
  const navigate = useNavigate();
  const { subject, gradeParam, practiceMode } = useParams();
  
  // Extract grade number from gradeParam (e.g., "grade-10" -> "10")
  const grade = gradeParam?.replace('grade-', '') || '';
  const gradeNumber = parseInt(grade);
  
  // Get topics for this subject and grade
  const topics = topicsBySubjectAndGrade[subject]?.[gradeNumber] || [];
  
  // Get subject configuration
  const subjectConfig = getSubjectConfig(subject);
  const formattedSubject = formatBreadcrumb(subject);
  const practiceModeDisplay = getPracticeModeDisplayName(practiceMode);

  if (!topics.length) {
    return (
      <div className="subject-page-container">
        <button onClick={() => navigate(-1)} className="back-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><path d="M12 19l-7-7 7-7"></path></svg>
        </button>
        <h1>Grade {grade} {formattedSubject} content coming soon!</h1>
      </div>
    );
  }

  return (
    <div className="subject-page-container">
      <button onClick={() => navigate(-1)} className="back-button">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><path d="M12 19l-7-7 7-7"></path></svg>
      </button>

      <header className="subject-page-header">
        <div className="subject-icon-wrapper" style={{ backgroundColor: subjectConfig.bgColor, color: subjectConfig.color }}>
          {subjectConfig.icon}
        </div>
        <div className="subject-title-group">
          <h1 style={{ color: subjectConfig.color }}>{practiceModeDisplay}</h1>
          <p>{formattedSubject} - Grade {grade}</p>
        </div>
      </header>

      <main className="topics-grid">
        {topics.map((topic) => (
          <Link 
            key={topic.title} 
            to={`/student/practice/${subject}/${gradeParam}/${practiceMode}/${topic.path}`} 
            className="topic-card-link"
          >
            <div className="topic-card-item">
              <div className="topic-details">
                <h3>{topic.title}</h3>
                <p>{topic.description}</p>
              </div>
              <div className="topic-arrow-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            </div>
          </Link>
        ))}
      </main>
    </div>
  );
}

export default SubtopicSelectionPage; 