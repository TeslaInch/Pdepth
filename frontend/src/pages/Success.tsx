import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { apiClient } from "@/services/apiClient";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";

export default function Success() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    // Paystack typically returns trxref and reference in the URL payload
    const reference = searchParams.get("reference") || searchParams.get("trxref");

    if (!reference) {
      setStatus("error");
      setErrorMsg("No payment reference found.");
      return;
    }

    let isMounted = true;

    async function verify() {
      try {
        await apiClient.verifyPayment(reference as string);
        if (isMounted) setStatus("success");
      } catch (e: any) {
        console.error("Payment verification failed", e);
        if (isMounted) {
          setStatus("error");
          setErrorMsg(e.message || "Payment verification failed.");
        }
      }
    }

    verify();

    return () => {
      isMounted = false;
    };
  }, [searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50/50">
      <div className="max-w-md w-full p-8 bg-white rounded-2xl shadow-card text-center">
        {status === "loading" && (
          <div className="flex flex-col items-center">
            <Loader2 className="h-12 w-12 text-primary animate-spin mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Verifying Payment...</h2>
            <p className="text-gray-500">Please wait while we confirm your transaction securely.</p>
          </div>
        )}

        {status === "success" && (
          <div className="flex flex-col items-center">
            <CheckCircle2 className="h-16 w-16 text-green-500 mb-4" />
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Payment Successful!</h2>
            <p className="text-gray-600 mb-6">
              Your account has been upgraded. You now have full access to PDepth Pro metrics.
            </p>
            <button
              onClick={() => navigate("/dashboard")}
              className="px-6 py-3 bg-primary text-white font-medium rounded-lg hover:bg-primary/90 transition-all shadow-sm w-full"
            >
              Go to Dashboard
            </button>
          </div>
        )}

        {status === "error" && (
          <div className="flex flex-col items-center">
            <XCircle className="h-16 w-16 text-red-500 mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Payment Failed</h2>
            <p className="text-gray-600 mb-6">{errorMsg || "We could not verify your payment at this time."}</p>
            <button
              onClick={() => navigate("/dashboard")}
              className="px-6 py-3 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-all w-full"
            >
              Return to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
