import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Политика конфиденциальности | AIM Agency",
  description:
    "Политика обработки персональных данных в соответствии с ФЗ-152. Как мы собираем, храним и защищаем ваши данные.",
  robots: { index: true, follow: true },
};

export default function PrivacyPolicyPage() {
  return (
    <main className="min-h-screen py-16 md:py-24 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="font-heading text-3xl md:text-4xl font-bold text-gray-900 mb-2">
          Политика конфиденциальности
        </h1>
        <p className="text-gray-500 mb-10">
          Последнее обновление: 18 мая 2026 г.
        </p>

        <div className="prose prose-gray max-w-none space-y-8">
          <section id="intro">
            <h2 className="font-heading text-xl font-bold text-gray-900 mb-3">
              1. Общие положения
            </h2>
            <p className="text-gray-700 leading-relaxed">
              Настоящая Политика конфиденциальности определяет порядок обработки и
              защиты персональных данных пользователей сайта{" "}
              <strong>iamaim.ru</strong> (далее — «Сайт») оператором — ИП
              AIM Agency (далее — «Оператор»). Обработка персональных данных
              осуществляется в соответствии с Федеральным законом № 152-ФЗ
              «О персональных данных».
            </p>
            <p className="text-gray-700 leading-relaxed">
              Используя Сайт, вы даёте согласие на обработку персональных данных
              в соответствии с настоящей Политикой. Если вы не согласны с
              условиями, пожалуйста, покиньте Сайт.
            </p>
          </section>

          <section id="data-collected">
            <h2 className="font-heading text-xl font-bold text-gray-900 mb-3">
              2. Какие данные мы собираем
            </h2>
            <p className="text-gray-700 leading-relaxed">
              Мы собираем только те данные, которые необходимы для оказания услуг:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>
                <strong>Контактные данные:</strong> имя, телефон, email — при
                заполнении формы на сайте.
              </li>
              <li>
                <strong>Информация о клинике:</strong> название, специализация —
                для подбора релевантных услуг.
              </li>
              <li>
                <strong>Технические данные:</strong> IP-адрес, файлы cookie,
                данные браузера — для аналитики и улучшения работы сайта.
              </li>
            </ul>
          </section>

          <section id="purposes">
            <h2 className="font-heading text-xl font-bold text-gray-900 mb-3">
              3. Цели обработки данных
            </h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>Оказание маркетинговых услуг и консультаций.</li>
              <li>Связь с пользователем по оставленной заявке.</li>
              <li>Улучшение качества работы Сайта через аналитику.</li>
              <li>
                Персонализация рекламных предложений (только при согласии на
                маркетинговые cookie).
              </li>
            </ul>
          </section>

          <section id="legal-basis">
            <h2 className="font-heading text-xl font-bold text-gray-900 mb-3">
              4. Правовое основание
            </h2>
            <p className="text-gray-700 leading-relaxed">
              Обработка персональных данных осуществляется на основании:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>
                Федерального закона от 27.07.2006 № 152-ФЗ «О персональных
                данных».
              </li>
              <li>
                Согласия субъекта персональных данных (ст. 9 ФЗ-152).
              </li>
              <li>
                Договора оказания услуг (ст. 6 ФЗ-152).
              </li>
            </ul>
          </section>

          <section id="storage">
            <h2 className="font-heading text-xl font-bold text-gray-900 mb-3">
              5. Хранение и защита данных
            </h2>
            <p className="text-gray-700 leading-relaxed">
              Персональные данные хранятся на серверах на территории Российской
              Федерации. Мы применяем следующие меры защиты:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>Шифрование данных при передаче (TLS 1.2+).</li>
              <li>Шифрование чувствительных полей в базе данных.</li>
              <li>Ограничение доступа к персональным данным.</li>
              <li>Регулярный аудит систем безопасности.</li>
            </ul>
          </section>

          <section id="retention">
            <h2 className="font-heading text-xl font-bold text-gray-900 mb-3">
              6. Срок хранения данных
            </h2>
            <p className="text-gray-700 leading-relaxed">
              Персональные данные хранятся в течение 7 лет с момента последнего
              взаимодействия (в соответствии с требованиями ФЗ-152). По истечении
              этого срока данные анонимизируются или удаляются автоматически.
            </p>
          </section>

          <section id="rights">
            <h2 className="font-heading text-xl font-bold text-gray-900 mb-3">
              7. Права субъекта данных
            </h2>
            <p className="text-gray-700 leading-relaxed">
              В соответствии с ФЗ-152 вы имеете право:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>Запросить информацию о хранимых данных.</li>
              <li>Потребовать уточнения или блокировки данных.</li>
              <li>
                Отозвать согласие на обработку (ст. 21 ФЗ-152).
              </li>
              <li>
                Потребовать удаления персональных данных (право на забвение).
              </li>
            </ul>
            <p className="text-gray-700 leading-relaxed mt-3">
              Для реализации прав обратитесь по email:{" "}
              <a
                href="mailto:privacy@iamaim.ru"
                className="text-primary-600 hover:text-primary-700 underline"
              >
                privacy@iamaim.ru
              </a>
              . Срок ответа — до 30 дней.
            </p>
          </section>

          <section id="cookies">
            <h2 className="font-heading text-xl font-bold text-gray-900 mb-3">
              8. Использование cookie-файлов
            </h2>
            <p className="text-gray-700 leading-relaxed">
              Сайт использует cookie-файлы трёх категорий:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>
                <strong>Необходимые</strong> — базовая функциональность сайта
                (всегда включены).
              </li>
              <li>
                <strong>Аналитические</strong> — Яндекс.Метрика для анализа
                трафика (требуется согласие).
              </li>
              <li>
                <strong>Маркетинговые</strong> — VK Pixel, MyTarget для
                персонализации рекламы (требуется согласие).
              </li>
            </ul>
            <p className="text-gray-700 leading-relaxed mt-3">
              Вы можете изменить настройки cookie в любое время, нажав на ссылку
              «Cookie-файлы» в футере сайта.
            </p>
          </section>

          <section id="third-party">
            <h2 className="font-heading text-xl font-bold text-gray-900 mb-3">
              9. Передача данных третьим лицам
            </h2>
            <p className="text-gray-700 leading-relaxed">
              Мы не продаём и не передаём персональные данные третьим лицам, за
              исключением случаев, предусмотренных законодательством РФ, или с
              вашего явного согласия.
            </p>
          </section>

          <section id="contacts">
            <h2 className="font-heading text-xl font-bold text-gray-900 mb-3">
              10. Контактная информация
            </h2>
            <div className="text-gray-700 leading-relaxed space-y-1">
              <p>
                <strong>Оператор:</strong> ИП AIM Agency
              </p>
              <p>
                <strong>Email:</strong>{" "}
                <a
                  href="mailto:privacy@iamaim.ru"
                  className="text-primary-600 hover:text-primary-700 underline"
                >
                  privacy@iamaim.ru
                </a>
              </p>
              <p>
                <strong>Телефон:</strong> +7 999 123-45-67
              </p>
              <p>
                <strong>Сайт:</strong> https://iamaim.ru
              </p>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
