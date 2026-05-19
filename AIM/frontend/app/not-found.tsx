import Link from "next/link";

export default function NotFound() {
  return (
    <main className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="text-8xl mb-6">🤷</div>
        <h1 className="font-heading text-4xl font-bold text-gray-900 mb-3">
          404
        </h1>
        <p className="text-lg text-gray-600 mb-2">
          Страница не найдена
        </p>
        <p className="text-sm text-gray-500 mb-8">
          Возможно, она устарела, удалена или её здесь никогда не было. Даже AI
          иногда ошибается.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/" className="btn-primary">
            На главную
          </Link>
          <Link href="/contact" className="btn-secondary">
            Написать нам
          </Link>
        </div>
      </div>
    </main>
  );
}
