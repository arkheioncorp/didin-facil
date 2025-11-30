import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const ChatbotBuilder = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Construtor de Chatbot</h1>
      <Card>
        <CardHeader>
          <CardTitle>Fluxos de Conversa</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Em breve: Crie fluxos de atendimento automatizado.</p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ChatbotBuilder;
