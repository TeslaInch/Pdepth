import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";
import { Upload, File, X, CheckCircle, AlertCircle, Clock } from "lucide-react";
import { supabase } from "@/supabaseClient";

interface UploadFile {
  id: string;
  file: File;
  status: "uploading" | "completed" | "error";
  error?: string;
  isLimitReached?: boolean;
  result?: any;
}

interface PDFUploadProps {
  onUploadComplete?: (result: any) => void;
}

const BACKEND_URL = import.meta.env.VITE_API_BASE_URL + "/upload-pdf";

const PDFUpload = ({ onUploadComplete }: PDFUploadProps) => {
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const showToast = (title: string, description: string, variant: "default" | "destructive" = "default") => {
    console.log(`Toast: ${title} - ${description} (${variant})`);
  };

  const handleUpgrade = async () => {
    try {
      const { apiClient } = await import("@/services/apiClient");
      const response = await apiClient.createCheckoutSession();
      if (response.url) {
        window.location.href = response.url;
      }
    } catch (e: any) {
      showToast("Checkout Failed", "Could not initialize checkout. Please try again later.", "destructive");
    }
  };

  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files || isProcessing) return;

    // Only allow one file at a time
    const file = files[0];
    if (!file) return;

    // Validate file type
    const validExtensions = ['pdf', 'txt', 'md', 'docx'];
    const ext = file.name.split('.').pop()?.toLowerCase();
    
    if (!ext || !validExtensions.includes(ext)) {
      showToast("Invalid file type", "Please upload only PDF, TXT, MD, or DOCX files.", "destructive");
      return;
    }

    // Validate file size (50MB max)
    if (file.size > 15 * 1024 * 1024) {
      showToast("File too large", "Please upload files smaller than 50MB.", "destructive");
      return;
    }

    const newFile: UploadFile = {
      id: Math.random().toString(36).substr(2, 9),
      file,
      status: "uploading",
    };

    setUploadFiles([newFile]);
    handleUpload(newFile);
  }, [isProcessing]);

  const handleUpload = async (uploadFile: UploadFile) => {
    try {
      setIsProcessing(true);

      const formData = new FormData();
      formData.append("file", uploadFile.file);

      console.log("Starting document upload and processing...");

      const { data: { session } } = await supabase.auth.getSession();

      const response = await fetch(BACKEND_URL, {
        method: "POST",
        headers: {
          ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {})
        },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw { ...data, status: response.status };
      }

      // Mark as completed
      setUploadFiles((prev) =>
        prev.map((file) =>
          file.id === uploadFile.id 
            ? { ...file, status: "completed", result: data } 
            : file
        )
      );

      // Notify parent component with complete results
      onUploadComplete?.(data);

      showToast(
        "Document processed successfully!",
        `${uploadFile.file.name} has been analyzed and summarized.`
      );

    } catch (err: any) {
      console.error("Upload/processing error:", err);
      
      // Since fetch parses API errors physically here, bypassing apiClient handles
      const isLimitError = err.isLimitReached || err.error === "limit_reached" || err.status === 429;
      
      // Convert UTC timestamp natively into the browser's local timezone standard
      const rawRetry = err.retryTime || err.retry_time;
      let parsedRetryTime = rawRetry;
      if (rawRetry) {
        try {
          parsedRetryTime = new Date(rawRetry).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          });
        } catch (e) {
          // Fallback if Date parser chokes on irregular shapes
          parsedRetryTime = rawRetry;
        }
      }

      if (!isLimitError) {
        showToast("Upload Failed", err.message || err.error || "An unexpected error occurred.", "destructive");
      }
      
      setUploadFiles((prev) =>
        prev.map((f) => {
          if (f.id === uploadFile.id) {
            if (isLimitError) {
              return { 
                ...f, 
                status: "error", // Keep status error to halt the progress bar, but flag it uniquely
                error: `Free plan allows 1 upload per hour. You can upload your next file at ${parsedRetryTime}.`,
                isLimitReached: true 
              };
            }
            return { 
              ...f, 
              status: "error", 
              error: err.message || err.error || "Upload failed" 
            };
          }
          return f;
        })
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const removeFile = (fileId: string) => {
    if (isProcessing) return; // Don't allow removal while processing
    setUploadFiles((prev) => prev.filter((file) => file.id !== fileId));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!isProcessing) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files);
  };

  return (
    <div className="space-y-6">
      <Card
        className={`border-2 border-dashed transition-all duration-200 ${
          isDragging 
            ? "border-blue-400 bg-blue-50" 
            : isProcessing 
            ? "border-gray-200 bg-gray-50" 
            : "border-gray-300 hover:border-gray-400"
        } ${isProcessing ? "pointer-events-none opacity-60" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <CardContent className="p-8 text-center">
          <div className={`p-4 rounded-full w-fit mx-auto mb-4 ${
            isProcessing ? "bg-orange-100" : "bg-blue-100"
          }`}>
            {isProcessing ? (
              <Clock className="h-8 w-8 text-orange-600 animate-pulse" />
            ) : (
              <Upload className="h-8 w-8 text-blue-600" />
            )}
          </div>

          {isProcessing ? (
            <>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Processing Your Document...</h3>
              <p className="text-gray-600 mb-6">
                AI is extracting text, generating summary, and finding related videos. 
                The processing time varies based on size.
              </p>
              <div className="flex items-center justify-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-sm text-gray-600">Please wait...</span>
              </div>
            </>
          ) : (
            <>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Drop your document here or click to browse
              </h3>
              <p className="text-gray-600 mb-6">
                Supports PDF, TXT, MD, DOCX up to 15MB • One file at a time
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Button
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                  size="lg"
                  onClick={() => document.getElementById("file-input")?.click()}
                  disabled={isProcessing}
                >
                  <File className="mr-2 h-4 w-4" /> Choose Document
                </Button>
                <div className="flex items-center text-gray-500 text-sm">
                  <AlertCircle className="mr-1 h-4 w-4" />
                  Complete processing takes 30-60 seconds
                </div>
              </div>
            </>
          )}

          <input
            id="file-input"
            type="file"
            accept=".pdf,.txt,.md,.docx"
            onChange={handleFileInput}
            className="hidden"
            disabled={isProcessing}
          />
        </CardContent>
      </Card>

      {uploadFiles.length > 0 && (
        <div className="space-y-4">
          {uploadFiles.map((uploadFile) => (
            <Card key={uploadFile.id} className="border shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${
                      uploadFile.status === "completed"
                        ? "bg-green-100"
                        : uploadFile.status === "error"
                        ? "bg-red-100"
                        : "bg-blue-100"
                    }`}>
                      {uploadFile.status === "completed" ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : uploadFile.status === "error" ? (
                        <AlertCircle className="h-5 w-5 text-red-600" />
                      ) : (
                        <div className="flex items-center space-x-2">
                          <Clock className="h-5 w-5 text-blue-600 animate-pulse" />
                        </div>
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{uploadFile.file.name}</p>
                      <p className="text-sm text-gray-500">
                        {(uploadFile.file.size / (1024 * 1024)).toFixed(1)} MB
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {uploadFile.status === "uploading" && (
                      <span className="text-sm text-blue-600 font-medium">Processing...</span>
                    )}
                    {uploadFile.status === "completed" && (
                      <span className="text-sm text-green-600 font-medium">✅ Complete</span>
                    )}
                    {uploadFile.status === "error" && !uploadFile.isLimitReached && (
                      <span className="text-sm text-red-600 font-medium">❌ Failed</span>
                    )}
                    {uploadFile.isLimitReached && (
                      <span className="text-sm text-amber-600 font-medium">⚠️ Limit Notice</span>
                    )}

                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => removeFile(uploadFile.id)} 
                      className="text-gray-400 hover:text-gray-600"
                      disabled={uploadFile.status === "uploading"}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {uploadFile.status === "uploading" && (
                  <div className="mt-3">
                    <Progress value={50} className="h-2" />
                    <p className="text-xs text-gray-500 mt-1">
                      Extracting text, generating summary, and finding related videos...
                    </p>
                  </div>
                )}

                {uploadFile.isLimitReached ? (
                  <div className="mt-4 p-4 rounded-md bg-amber-50 border border-amber-200 flex flex-col sm:flex-row items-start sm:items-center space-y-3 sm:space-y-0 sm:space-x-4">
                    <div className="flex-1 flex items-start space-x-3">
                      <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
                      <div>
                        <h4 className="text-sm font-semibold text-amber-800">Upload Limit Notice</h4>
                        <p className="text-sm text-amber-700 mt-1">{uploadFile.error}</p>
                      </div>
                    </div>
                    <Button 
                      onClick={handleUpgrade} 
                      className="bg-amber-600 hover:bg-amber-700 text-white shadow-sm flex-shrink-0 w-full sm:w-auto text-xs"
                      size="sm"
                    >
                      Upgrade to Pro for unlimited uploads.
                    </Button>
                  </div>
                ) : uploadFile.error ? (
                  <div className="mt-4 p-4 rounded-md bg-red-50 border border-red-200 flex items-start space-x-3">
                    <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <h4 className="text-sm font-semibold text-red-800">Upload Failed</h4>
                      <p className="text-sm text-red-600 mt-1">{uploadFile.error}</p>
                    </div>
                  </div>
                ) : null}

                {uploadFile.status === "completed" && uploadFile.result && (
                  <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
                    <p className="text-sm text-green-700 flex items-start">
                      <CheckCircle className="mr-2 h-4 w-4 mt-0.5 flex-shrink-0" />
                      <span>{uploadFile.result.message || "Processed successfully!"}</span>
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default PDFUpload;