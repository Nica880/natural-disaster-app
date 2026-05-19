import { useState } from 'react'
import { fetchFileApiData } from './services/api'

function FileApi() {
  const [data, setData] = useState(null)

  const handleFetch = async () => {
    const result = await fetchFileApiData()
    setData(result)


  }

  return (
    <div className="p-5 bg-gray-100 min-h-screen">
      <h2 className="text-gray-800 text-2xl mb-5">File API Results</h2>
      <button 
        onClick={handleFetch}
        className="px-5 py-2.5 bg-gray-600 text-white border-none rounded cursor-pointer mb-5 hover:bg-gray-700"
      >
        Fetch Results
      </button>
      {data ? (
        <div>
          {data.image && (
            <img 
              src={data.image} 
              alt="Uploaded" 
              className="max-w-md rounded-lg mb-5 border border-gray-300"
            />
          )}
          <div className="flex gap-4 flex-wrap">
            <div className="bg-white p-5 px-7 rounded-xl shadow-md min-w-[200px]">
              <div className="text-gray-500 text-xs mb-1">CLASS</div>
              <div className="text-gray-800 text-2xl font-semibold">{data.class}</div>
            </div>
            <div className="bg-white p-5 px-7 rounded-xl shadow-md min-w-[200px]">
              <div className="text-gray-500 text-xs mb-1">CONFIDENCE</div>
              <div className="text-gray-800 text-2xl font-semibold">
                {(data.confidence * 100).toFixed(2)}%
              </div>
            </div>
          </div>
        </div>
      ) : (
        <p className="text-gray-500">Waiting for data...</p>
      )}
    </div>
  )
}

export default FileApi
