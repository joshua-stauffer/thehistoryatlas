import { InMemoryCache } from "@apollo/client";
import { historyBackVar } from "../hooks/history";

export const cache: InMemoryCache = new InMemoryCache({
  typePolicies: {
    ManifestQuery: {
      keyFields: ["GUID"],
    },
    SummaryQuery: {
      keyFields: ["GUID"],
    },
    History: {
      keyFields: ["GUID"],
      fields: {
        back: {
          read() {
            const all = historyBackVar();
            return all[all.length - 1];
          },
        },
      },
    },
  },
});
