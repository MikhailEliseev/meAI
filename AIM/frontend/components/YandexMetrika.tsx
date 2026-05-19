"use client";

import { useEffect } from "react";
import { useCookieConsent } from "@/components/CookieConsent";

export function YandexMetrika() {
  const consent = useCookieConsent();
  const metrikaId = process.env.NEXT_PUBLIC_YANDEX_METRIKA_ID;

  useEffect(() => {
    if (!consent?.analytics || !metrikaId) return;
    if (typeof window === "undefined") return;

    if ((window as any).ym) return;

    const script = document.createElement("script");
    script.text = `
      (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
      m[i].l=1*new Date();
      k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
      (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");
      ym(${metrikaId}, "init", {
        clickmap:true,
        trackLinks:true,
        accurateTrackBounce:true,
        webvisor:true,
        ecommerce:"dataLayer"
      });
    `;
    document.head.appendChild(script);

    const noscript = document.createElement("noscript");
    noscript.innerHTML = `<div><img src="https://mc.yandex.ru/watch/${metrikaId}" style="position:absolute;left:-9999px" alt="" /></div>`;
    document.body.appendChild(noscript);
  }, [consent?.analytics, metrikaId]);

  return null;
}
