export default function ResultDisplay({ result }) {
  return (
    <div className="mt-8 space-y-4">
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-indigo-900 mb-2">
          {result.class}
        </h2>
        <p className="text-lg text-indigo-700">
          Confidence: {(result.confidence * 100).toFixed(2)}%
        </p>
      </div>

      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">All Probabilities</h3>
        <div className="space-y-2">
          {Object.entries(result.probabilities).map(([cls, prob]) => (
            <div key={cls} className="flex justify-between items-center">
              <span className="text-gray-700">{cls}</span>
              <div className="flex items-center gap-2 flex-1 ml-4">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-indigo-600 h-2 rounded-full transition-all"
                    style={{ width: `${prob * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600 w-16 text-right">
                  {(prob * 100).toFixed(2)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
