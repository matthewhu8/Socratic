import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Youtube, Brain, Bot, PlayCircle, Zap, MessageSquare } from "lucide-react";

const StudyModes = () => {
  const studyModes = [
    {
      id: "youtube",
      title: "YouTube Assisted Learning",
      description: "Learn with curated video content from top educators worldwide",
      icon: Youtube,
      color: "text-red-500",
      bgGradient: "from-red-50 to-pink-50",
      features: ["Curated playlists", "Interactive notes", "Progress tracking"],
      buttonText: "Start Learning",
      buttonIcon: PlayCircle,
    },
    {
      id: "dynamic",
      title: "Dynamic Learning",
      description: "Adaptive learning paths that adjust to your pace and understanding",
      icon: Brain,
      color: "text-primary",
      bgGradient: "from-purple-50 to-blue-50",
      features: ["Adaptive content", "Real-time feedback", "Personalized paths"],
      buttonText: "Begin Learning",
      buttonIcon: Zap,
    },
    {
      id: "ai-tutor",
      title: "AI Tutor",
      description: "Get instant help and explanations from our intelligent AI assistant",
      icon: Bot,
      color: "text-emerald-500",
      bgGradient: "from-emerald-50 to-teal-50",
      features: ["24/7 availability", "Instant responses", "Concept clarification"],
      buttonText: "Chat Now",
      buttonIcon: MessageSquare,
    },
  ];

  return (
    <section className="w-full max-w-7xl mx-auto px-6 py-12">
      <div className="text-center mb-12">
        <h2 className="text-4xl font-bold mb-4 bg-gradient-hero bg-clip-text text-transparent">
          Choose Your Learning Journey
        </h2>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Select the perfect study mode that matches your learning style and goals
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {studyModes.map((mode) => {
          const IconComponent = mode.icon;
          const ButtonIcon = mode.buttonIcon;
          
          return (
            <Card 
              key={mode.id}
              className="group hover:shadow-primary transition-all duration-300 hover:-translate-y-2 border-border/50 bg-gradient-card"
            >
              <CardHeader className="text-center pb-4">
                <div className={`w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br ${mode.bgGradient} flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                  <IconComponent className={`w-8 h-8 ${mode.color}`} />
                </div>
                <CardTitle className="text-xl font-bold text-foreground">
                  {mode.title}
                </CardTitle>
                <CardDescription className="text-muted-foreground">
                  {mode.description}
                </CardDescription>
              </CardHeader>
              
              <CardContent className="space-y-6">
                <ul className="space-y-2">
                  {mode.features.map((feature, index) => (
                    <li key={index} className="flex items-center text-sm text-muted-foreground">
                      <div className="w-2 h-2 bg-primary rounded-full mr-3"></div>
                      {feature}
                    </li>
                  ))}
                </ul>
                
                <Button 
                  variant="study" 
                  className="w-full group-hover:bg-primary group-hover:text-primary-foreground"
                  size="lg"
                >
                  <ButtonIcon size={18} />
                  {mode.buttonText}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </section>
  );
};

export default StudyModes;