import React from "react";
import { ThemeProvider } from "@mui/material/styles";

import { GenericError } from "./pages/errorPages";

import { theme } from "./baseStyle";
import { HistoryEventView } from "./pages/historyEvent/historyEventView";

import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { historyEventLoader } from "./pages/historyEvent/historyEventLoader";

function App() {
  const router = createBrowserRouter([
    {
      path: "/",
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
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}

export default App;
