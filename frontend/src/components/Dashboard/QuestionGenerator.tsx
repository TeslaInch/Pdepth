import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  X,
  Loader2,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  BookOpenCheck,
  PenLine,
} from "lucide-react";
import { apiClient } from "@/services/apiClient";

interface MCQQuestion {
  question: string;
  options: Record<string, string>;
  correct_answer: string;
  explanation: string;
}

interface EssayQuestion {
  question: string;
  suggested_answer: string;
}

interface QuestionGeneratorProps {
  summaryText: string;
  isOpen: boolean;
  onClose: () => void;
  pdfTitle: string;
}

const QuestionGenerator = ({
  summaryText,
  isOpen,
  onClose,
  pdfTitle,
}: QuestionGeneratorProps) => {
  const [questionType, setQuestionType] = useState<"mcq" | "essay" | "both">(
    "mcq"
  );
  const [difficulty, setDifficulty] = useState<"easy" | "medium" | "hard">(
    "medium"
  );
  const [count, setCount] = useState(5);
  const [isLoading, setIsLoading] = useState(false);
  const [mcqQuestions, setMcqQuestions] = useState<MCQQuestion[]>([]);
  const [essayQuestions, setEssayQuestions] = useState<EssayQuestion[]>([]);
  const [selectedAnswers, setSelectedAnswers] = useState<
    Record<number, string>
  >({});
  const [revealedAnswers, setRevealedAnswers] = useState<Set<number>>(
    new Set()
  );
  const [expandedEssay, setExpandedEssay] = useState<Set<number>>(new Set());
  const [error, setError] = useState("");
  const [generated, setGenerated] = useState(false);

  const handleGenerate = async () => {
    setIsLoading(true);
    setError("");
    setMcqQuestions([]);
    setEssayQuestions([]);
    setSelectedAnswers({});
    setRevealedAnswers(new Set());
    setExpandedEssay(new Set());

    try {
      const response = await apiClient.generateQuestions(
        summaryText,
        questionType,
        difficulty,
        count
      );

      const data = response.data as Record<string, unknown[]>;

      if (data.mcq) setMcqQuestions(data.mcq as MCQQuestion[]);
      if (data.essay) setEssayQuestions(data.essay as EssayQuestion[]);
      setGenerated(true);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : "Unknown error";
      if (errMsg.includes("403")) {
        setError(
          "Essay questions require a paid plan. Try MCQ only, or upgrade your plan."
        );
      } else {
        setError(`Failed to generate questions. ${errMsg}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const selectAnswer = (qIndex: number, option: string) => {
    if (revealedAnswers.has(qIndex)) return;
    setSelectedAnswers((prev) => ({ ...prev, [qIndex]: option }));
  };

  const revealAnswer = (qIndex: number) => {
    setRevealedAnswers((prev) => new Set(prev).add(qIndex));
  };

  const toggleEssay = (qIndex: number) => {
    setExpandedEssay((prev) => {
      const copy = new Set(prev);
      copy.has(qIndex) ? copy.delete(qIndex) : copy.add(qIndex);
      return copy;
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div
        className="w-full max-w-2xl mx-4 bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden"
        style={{ maxHeight: "90vh" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b bg-gradient-to-r from-purple-600 to-indigo-600">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg">
              <BrainCircuit className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="text-white font-semibold text-sm">
                Generate Questions
              </h3>
              <p className="text-white/70 text-xs truncate max-w-[300px]">
                {pdfTitle}
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-white hover:bg-white/20 rounded-full h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Config Panel */}
          {!generated && (
            <div className="space-y-4">
              {/* Question Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Question Type
                </label>
                <div className="flex gap-2">
                  {(["mcq", "essay", "both"] as const).map((type) => (
                    <button
                      key={type}
                      onClick={() => setQuestionType(type)}
                      className={`flex-1 px-3 py-2.5 rounded-lg border text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                        questionType === type
                          ? "bg-purple-600 text-white border-purple-600"
                          : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
                      }`}
                    >
                      {type === "mcq" && (
                        <BookOpenCheck className="h-4 w-4" />
                      )}
                      {type === "essay" && <PenLine className="h-4 w-4" />}
                      {type === "both" && (
                        <BrainCircuit className="h-4 w-4" />
                      )}
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Difficulty */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Difficulty
                </label>
                <div className="flex gap-2">
                  {(["easy", "medium", "hard"] as const).map((d) => (
                    <button
                      key={d}
                      onClick={() => setDifficulty(d)}
                      className={`flex-1 px-3 py-2.5 rounded-lg border text-sm font-medium transition-all ${
                        difficulty === d
                          ? d === "easy"
                            ? "bg-green-600 text-white border-green-600"
                            : d === "medium"
                            ? "bg-yellow-500 text-white border-yellow-500"
                            : "bg-red-600 text-white border-red-600"
                          : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
                      }`}
                    >
                      {d.charAt(0).toUpperCase() + d.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Count */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Number of Questions: {count}
                </label>
                <input
                  type="range"
                  min="3"
                  max="10"
                  value={count}
                  onChange={(e) => setCount(Number(e.target.value))}
                  className="w-full accent-purple-600"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>3</span>
                  <span>10</span>
                </div>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              {/* Generate Button */}
              <Button
                onClick={handleGenerate}
                disabled={isLoading}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white py-3 text-sm font-medium"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <BrainCircuit className="mr-2 h-4 w-4" />
                    Generate Questions
                  </>
                )}
              </Button>
            </div>
          )}

          {/* MCQ Results */}
          {mcqQuestions.length > 0 && (
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-800 flex items-center gap-2">
                <BookOpenCheck className="h-5 w-5 text-purple-600" />
                Multiple Choice Questions
              </h4>
              {mcqQuestions.map((q, qIdx) => (
                <div
                  key={qIdx}
                  className="bg-gray-50 rounded-xl p-4 space-y-3 border"
                >
                  <p className="font-medium text-gray-900 text-sm">
                    {qIdx + 1}. {q.question}
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {Object.entries(q.options).map(([key, value]) => {
                      const isSelected = selectedAnswers[qIdx] === key;
                      const isRevealed = revealedAnswers.has(qIdx);
                      const isCorrect = key === q.correct_answer;

                      let btnClass =
                        "text-left px-3 py-2 rounded-lg border text-sm transition-all ";
                      if (isRevealed) {
                        if (isCorrect)
                          btnClass +=
                            "bg-green-100 border-green-400 text-green-800";
                        else if (isSelected && !isCorrect)
                          btnClass +=
                            "bg-red-100 border-red-400 text-red-800";
                        else btnClass += "bg-white border-gray-200 text-gray-500";
                      } else if (isSelected) {
                        btnClass +=
                          "bg-purple-100 border-purple-400 text-purple-800";
                      } else {
                        btnClass +=
                          "bg-white border-gray-200 text-gray-700 hover:bg-gray-100";
                      }

                      return (
                        <button
                          key={key}
                          onClick={() => selectAnswer(qIdx, key)}
                          className={btnClass}
                          disabled={isRevealed}
                        >
                          <span className="font-semibold mr-2">{key}.</span>
                          {value}
                        </button>
                      );
                    })}
                  </div>
                  {selectedAnswers[qIdx] && !revealedAnswers.has(qIdx) && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => revealAnswer(qIdx)}
                      className="text-xs"
                    >
                      <CheckCircle2 className="mr-1 h-3 w-3" />
                      Check Answer
                    </Button>
                  )}
                  {revealedAnswers.has(qIdx) && q.explanation && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-800">
                      <strong>Explanation:</strong> {q.explanation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Essay Results */}
          {essayQuestions.length > 0 && (
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-800 flex items-center gap-2">
                <PenLine className="h-5 w-5 text-indigo-600" />
                Essay Questions
              </h4>
              {essayQuestions.map((q, qIdx) => (
                <div
                  key={qIdx}
                  className="bg-gray-50 rounded-xl p-4 space-y-2 border"
                >
                  <p className="font-medium text-gray-900 text-sm">
                    {qIdx + 1}. {q.question}
                  </p>
                  <button
                    onClick={() => toggleEssay(qIdx)}
                    className="text-xs text-indigo-600 flex items-center gap-1 hover:underline"
                  >
                    {expandedEssay.has(qIdx) ? (
                      <>
                        <ChevronUp className="h-3 w-3" /> Hide Model Answer
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-3 w-3" /> Show Model Answer
                      </>
                    )}
                  </button>
                  {expandedEssay.has(qIdx) && (
                    <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 text-xs text-indigo-800">
                      {q.suggested_answer}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Regenerate */}
          {generated && (
            <Button
              variant="outline"
              onClick={() => {
                setGenerated(false);
                setMcqQuestions([]);
                setEssayQuestions([]);
                setSelectedAnswers({});
                setRevealedAnswers(new Set());
                setExpandedEssay(new Set());
                setError("");
              }}
              className="w-full text-sm"
            >
              <BrainCircuit className="mr-2 h-4 w-4" />
              Generate New Questions
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuestionGenerator;
