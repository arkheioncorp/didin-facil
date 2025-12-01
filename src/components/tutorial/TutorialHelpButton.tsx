/**
 * Tutorial Help Button
 * ====================
 * Botão de ajuda que aparece no Header para iniciar tutoriais.
 */

import * as React from "react";
import { HelpCircle, BookOpen, Play, Check, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { useTutorial, TUTORIALS } from "./TutorialProvider";
import { useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

export const TutorialHelpButton: React.FC = () => {
  const { startTutorial, completedTutorials, resetTutorials } = useTutorial();
  const location = useLocation();

  // Get tutorials relevant to current page
  const currentPageTutorials = TUTORIALS.filter(
    (t) => t.triggerOnPage === location.pathname || t.id === "main-onboarding"
  );

  // Check if onboarding was completed
  const onboardingCompleted = completedTutorials.includes("main-onboarding");

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={cn(
            "relative h-9 w-9 rounded-full",
            !onboardingCompleted && "animate-pulse"
          )}
        >
          <HelpCircle className="h-5 w-5" />
          {!onboardingCompleted && (
            <span className="absolute -top-0.5 -right-0.5 h-3 w-3 rounded-full bg-primary animate-ping" />
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-72">
        <DropdownMenuLabel className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-primary" />
          Tutoriais & Ajuda
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {/* Main Onboarding */}
        <DropdownMenuItem
          onClick={() => startTutorial("main-onboarding")}
          className="flex items-center justify-between cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <Play className="h-4 w-4 text-primary" />
            <span>Tour Completo</span>
          </div>
          {completedTutorials.includes("main-onboarding") ? (
            <Badge variant="secondary" className="text-xs">
              <Check className="h-3 w-3 mr-1" />
              Concluído
            </Badge>
          ) : (
            <Badge className="text-xs bg-primary/20 text-primary border-primary/30">
              Novo
            </Badge>
          )}
        </DropdownMenuItem>

        {/* Page-specific tutorials */}
        {currentPageTutorials.length > 0 && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              Tutoriais desta página
            </DropdownMenuLabel>
            {currentPageTutorials
              .filter((t) => t.id !== "main-onboarding")
              .map((tutorial) => (
                <DropdownMenuItem
                  key={tutorial.id}
                  onClick={() => startTutorial(tutorial.id)}
                  className="flex items-center justify-between cursor-pointer"
                >
                  <div className="flex flex-col">
                    <span className="text-sm">{tutorial.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {tutorial.description}
                    </span>
                  </div>
                  {completedTutorials.includes(tutorial.id) && (
                    <Check className="h-4 w-4 text-green-500" />
                  )}
                </DropdownMenuItem>
              ))}
          </>
        )}

        {/* All tutorials */}
        <DropdownMenuSeparator />
        <DropdownMenuLabel className="text-xs text-muted-foreground">
          Todos os tutoriais
        </DropdownMenuLabel>
        {TUTORIALS.filter((t) => t.id !== "main-onboarding").map((tutorial) => (
          <DropdownMenuItem
            key={tutorial.id}
            onClick={() => startTutorial(tutorial.id)}
            className="flex items-center justify-between cursor-pointer"
          >
            <span className="text-sm">{tutorial.name}</span>
            {completedTutorials.includes(tutorial.id) && (
              <Check className="h-4 w-4 text-green-500" />
            )}
          </DropdownMenuItem>
        ))}

        {/* Reset */}
        {completedTutorials.length > 0 && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={resetTutorials}
              className="text-muted-foreground cursor-pointer"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Resetar tutoriais
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default TutorialHelpButton;
