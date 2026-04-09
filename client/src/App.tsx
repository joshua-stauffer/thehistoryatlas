import React from "react";
import { ThemeProvider } from "@mui/material/styles";

import { GenericError } from "./pages/errorPages";

import { theme } from "./baseStyle";
import { AuthProvider } from "./auth/authContext";
import { HistoryEventView } from "./pages/historyEvent/historyEventView";
import { FeedView } from "./pages/feed/feedView";

import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { historyEventLoader } from "./pages/historyEvent/historyEventLoader";
import { feedLoader } from "./pages/feed/feedLoader";

function App() {
  const router = createBrowserRouter([
    {
      path: "/",
      element: <FeedView />,
      loader: feedLoader,
      errorElement: (
        <GenericError
          header={"Uh oh..."}
          text={"Something went wrong"}
          details={"Please try again"}
        />
      ),
    },
    {
      path: "/stories/:storyId",
      element: <HistoryEventView />,
      loader: historyEventLoader,
      errorElement: (
        <GenericError
          header={"Uh oh..."}
          text={"Something went wrong"}
          details={"Check the URL and try again"}
        />
      ),
    },
    {
      path: "/stories/:storyId/events/:eventId",
      element: <HistoryEventView />,
      loader: historyEventLoader,
      errorElement: (
        <GenericError
          header={"Uh oh..."}
          text={"Something went wrong"}
          details={"Check the URL and try again"}
        />
      ),
    },
  ]);
  return (
    <ThemeProvider theme={theme}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
