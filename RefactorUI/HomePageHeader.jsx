import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ChevronDown, User } from "lucide-react";

const Header = () => {
  const [selectedGrade, setSelectedGrade] = useState<string>("Grade 10");

  const grades = ["Grade 9", "Grade 10", "Grade 11", "Grade 12"];

  return (
    <header className="w-full py-6 px-6 flex justify-between items-center bg-background/80 backdrop-blur-sm border-b border-border">
      <div className="flex items-center space-x-6">
        <div className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
          EduLearn
        </div>
        <Link to="/progress">
          <Button variant="ghost" className="text-sm text-muted-foreground hover:text-primary">
            Progress
          </Button>
        </Link>
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button 
            variant="ghost" 
            className="flex items-center space-x-2 hover:bg-primary/10 transition-all duration-200"
          >
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-primary/10 text-primary">
                <User size={16} />
              </AvatarFallback>
            </Avatar>
            <span className="text-sm font-medium hidden sm:inline">{selectedGrade}</span>
            <ChevronDown size={16} className="text-muted-foreground" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent 
          align="end" 
          className="w-40 bg-popover/95 backdrop-blur-sm border border-border shadow-card"
        >
          {grades.map((grade) => (
            <DropdownMenuItem
              key={grade}
              onClick={() => setSelectedGrade(grade)}
              className={`cursor-pointer transition-all duration-200 ${
                selectedGrade === grade
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-primary/10"
              }`}
            >
              {grade}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
};

export default Header;