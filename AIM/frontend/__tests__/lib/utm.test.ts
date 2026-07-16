/**
 * UTM tracking tests — parse, store, retrieve
 */
import { getStoredUtm } from "@/components/UTMCapture";

describe("UTM Capture", () => {
  beforeEach(() => {
    sessionStorage.clear();
    // Clear cookies
    document.cookie.split(";").forEach((c) => {
      document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
    });
  });

  describe("getStoredUtm", () => {
    it("returns empty object when nothing stored", () => {
      const utm = getStoredUtm();
      expect(utm).toEqual({});
    });

    it("returns stored UTM params from sessionStorage", () => {
      const params = {
        utm_source: "yandex",
        utm_medium: "cpc",
        utm_campaign: "launch",
      };
      sessionStorage.setItem("aim_utm", JSON.stringify(params));

      const utm = getStoredUtm();
      expect(utm).toEqual(params);
    });

    it("handles corrupt sessionStorage data gracefully", () => {
      sessionStorage.setItem("aim_utm", "not-valid-json");

      const utm = getStoredUtm();
      expect(utm).toEqual({});
    });

    it("returns all UTM fields when present", () => {
      const params = {
        utm_source: "yandex",
        utm_medium: "cpc",
        utm_campaign: "launch_2026",
        utm_term: "ai_marketing",
        utm_content: "banner_top",
      };
      sessionStorage.setItem("aim_utm", JSON.stringify(params));

      const utm = getStoredUtm();
      expect(utm.utm_source).toBe("yandex");
      expect(utm.utm_medium).toBe("cpc");
      expect(utm.utm_campaign).toBe("launch_2026");
      expect(utm.utm_term).toBe("ai_marketing");
      expect(utm.utm_content).toBe("banner_top");
    });
  });
});
