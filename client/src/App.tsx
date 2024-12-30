import React from "react";
import { ThemeProvider } from "@mui/material/styles";

import { GenericError } from "./pages/errorPages";


import { theme } from "./baseStyle";
import { HistoryEventView } from "./pages/historyEvent/historyEventView";

import { createBrowserRouter, RouterProvider } from "react-router-dom";
import {
  LandingPage,
  landingPageLoader,
} from "./pages/historyEvent/landingPage";
import { historyEventLoader } from "./pages/historyEvent/historyEventLoader";

function App() {
  const router = createBrowserRouter([
    {
      path: "/",
      element: <LandingPage />,
      loader: landingPageLoader,
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
