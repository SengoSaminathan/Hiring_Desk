"use client";

import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Global Query Client Configuration
 * - staleTime: 60,000ms (1 minute) to eliminate redundant network re-queries
 * - gcTime: 15 minutes
 * - refetchOnWindowFocus: false to avoid sudden jarring background table shifts
 */
function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60000,
        gcTime: 1000 * 60 * 15,
        refetchOnWindowFocus: false,
        retry: 1,
      },
    },
  });
}

let browserQueryClient = undefined;

export function getQueryClient() {
  if (typeof window === "undefined") {
    // Server: always create a new query client
    return createQueryClient();
  }
  // Browser: keep singleton query client
  if (!browserQueryClient) {
    browserQueryClient = createQueryClient();
  }
  return browserQueryClient;
}

export function QueryProvider({ children }) {
  // Use state to guarantee client is retained across renders in the browser
  const [queryClient] = useState(() => getQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

export default QueryProvider;
