import React from "react";
import { ThemeProvider } from "@mui/material/styles";

import { GenericError, ResourceNotFoundError } from "./pages/errorPages";
import { AddEventPage } from "./pages/addEvent";

import { useTokenManager } from "./hooks/token";

import { theme } from "./baseStyle";
import { HistoryEventView } from "./pages/historyEvent/historyEventView";

import { createBrowserRouter, RouterProvider } from "react-router-dom";
import {
  LandingPage,
  landingPageLoader,
} from "./pages/historyEvent/landingPage";
import {
  historyEventLoader,
  fakeHistoryEventLoader,
} from "./pages/historyEvent/historyEventLoader";

function App() {
  const tokenManager = useTokenManager();
  const router = createBrowserRouter([
    {
      path: "/",
      element: <LandingPage />,
      loader: landingPageLoader,
    },
    {
      path: "/stories/:storyId/events/:eventId",
      element: <HistoryEventView />,
      loader: fakeHistoryEventLoader,
      errorElement: (
        <GenericError
          header={"Uh oh..."}
          text={"Something went wrong"}
          details={"Check the URL and try again"}
        />
      ),
    },
    {
      path: "/add-event",
      element: <AddEventPage tokenManager={tokenManager} />,
    },
  ]);
  return (
    <ThemeProvider theme={theme}>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}

export default App;
