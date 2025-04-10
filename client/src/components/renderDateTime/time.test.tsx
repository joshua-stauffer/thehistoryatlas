import { renderDateTime } from "./time";
import { CalendarDate } from "../../graphql/events";

describe("renderDateTime", () => {
  const makeDate = (datetime: string, precision: number): CalendarDate => ({
    datetime,
    calendar: "http://www.wikidata.org/entity/Q1985727",
    precision,
  });

  describe("year precision (9)", () => {
    it("handles CE years correctly", () => {
      const date = makeDate("+1234-01-01T00:00:00Z", 9);
      expect(renderDateTime(date)).toBe("1234");
    });

    it("handles BCE years correctly", () => {
      const date = makeDate("-0753-01-01T00:00:00Z", 9);
      expect(renderDateTime(date)).toBe("753 B.C.E.");
    });

    it("handles year 0", () => {
      const date = makeDate("+0000-01-01T00:00:00Z", 9);
      expect(renderDateTime(date)).toBe("0");
    });
  });

  describe("month precision (10)", () => {
    it("handles CE months correctly", () => {
      const date = makeDate("+1234-06-01T00:00:00Z", 10);
      expect(renderDateTime(date)).toBe("June of 1234");
    });

    it("handles BCE months correctly", () => {
      const date = makeDate("-0753-06-01T00:00:00Z", 10);
      expect(renderDateTime(date)).toBe("June of -753");
    });
  });

  describe("day precision (11)", () => {
    it("handles CE days correctly", () => {
      const date = makeDate("+1234-06-15T00:00:00Z", 11);
      const result = renderDateTime(date);
      // Don't test the weekday since it can't be reliably determined for historical dates
      expect(result).toMatch(/^[A-Za-z]+ June 15th, 1234$/);
    });

    it("handles BCE days correctly", () => {
      const date = makeDate("-0753-06-15T00:00:00Z", 11);
      const result = renderDateTime(date);
      // Don't test the weekday since it can't be reliably determined for historical dates
      expect(result).toMatch(/^[A-Za-z]+ June 15th, -753$/);
    });
  });

  describe("decade precision (8)", () => {
    it("handles CE decades correctly", () => {
      const date = makeDate("+1230-01-01T00:00:00Z", 8);
      expect(renderDateTime(date)).toBe("1230s");
    });

    it("handles BCE decades correctly", () => {
      const date = makeDate("-0750-01-01T00:00:00Z", 8);
      expect(renderDateTime(date)).toBe("750s B.C.E.");
    });
  });

  describe("century precision (7)", () => {
    it("handles CE centuries correctly", () => {
      const date = makeDate("+1200-01-01T00:00:00Z", 7);
      expect(renderDateTime(date)).toBe("1200s");
    });

    it("handles BCE centuries correctly", () => {
      const date = makeDate("-0700-01-01T00:00:00Z", 7);
      expect(renderDateTime(date)).toBe("700s B.C.E.");
    });
  });
}); 