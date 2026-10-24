import React, { createContext, useContext, useState, useEffect, useRef } from 'react'
import { datasetAPI, aiAPI } from '../api/client'

const StoreContext = createContext(null)

// In-memory module cache to ensure instantaneous tab switching across datasets
const storeDataCache = new Map()

export function StoreProvider({ children }) {
  const [datasets, setDatasets] = useState([])
  const [activeDatasetId, setActiveDatasetId] = useState(() => {
    return localStorage.getItem('tp_active_dataset') || '10'
  })
  
  // Initialize with cached record if available
  const cachedInitial = storeDataCache.get(String(localStorage.getItem('tp_active_dataset') || '10'))

  const [dataset, setDataset] = useState(() => cachedInitial?.dataset || null)
  const [result, setResult] = useState(() => cachedInitial?.result || null)
  const [diagnosis, setDiagnosis] = useState(() => cachedInitial?.diagnosis || null)
  const [loading, setLoading] = useState(() => !cachedInitial?.result)
  const [diagnosisLoading, setDiagnosisLoading] = useState(() => !cachedInitial?.diagnosis)

  // 1. Fetch available datasets list on initial mount
  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    try {
      const res = await datasetAPI.list()
      const list = res.data.datasets || []
      setDatasets(list)

      // If activeDatasetId is not in list, fallback to latest completed dataset
      if (list.length > 0) {
        const completed = list.filter(d => d.status === 'completed')
        const defaultId = completed.length > 0 ? completed[0].id : list[0].id
        
        setActiveDatasetId(prev => {
          if (prev && list.some(d => String(d.id) === String(prev))) {
            return String(prev)
          }
          localStorage.setItem('tp_active_dataset', String(defaultId))
          return String(defaultId)
        })
      }
    } catch (err) {
      console.warn('Failed to load datasets list:', err)
    }
  }

  // 2. Fetch active dataset details & diagnosis whenever activeDatasetId changes
  useEffect(() => {
    if (!activeDatasetId) return

    const strId = String(activeDatasetId)
    localStorage.setItem('tp_active_dataset', strId)

    // Check if we have cached data for instant display (0ms lag)
    const cached = storeDataCache.get(strId)
    if (cached) {
      if (cached.dataset) setDataset(cached.dataset)
      if (cached.result) setResult(cached.result)
      if (cached.diagnosis) setDiagnosis(cached.diagnosis)
      setLoading(false)
      setDiagnosisLoading(false)
    } else {
      setLoading(true)
      setDiagnosisLoading(true)
    }

    let isMounted = true

    // Fetch main dataset record
    datasetAPI.get(strId)
      .then((res) => {
        if (!isMounted) return
        const ds = res.data || {}
        const resObj = ds.result || {}
        setDataset(ds)
        setResult(resObj)

        // Save to cache
        const prevCache = storeDataCache.get(strId) || {}
        storeDataCache.set(strId, {
          ...prevCache,
          dataset: ds,
          result: resObj,
        })
      })
      .catch((err) => {
        console.error('Failed to load active dataset:', err)
      })
      .finally(() => {
        if (isMounted) setLoading(false)
      })

    // Fetch AI diagnosis in parallel
    aiAPI.diagnosis(strId)
      .then((res) => {
        if (!isMounted) return
        const diagData = res.data || null
        setDiagnosis(diagData)

        // Save to cache
        const prevCache = storeDataCache.get(strId) || {}
        storeDataCache.set(strId, {
          ...prevCache,
          diagnosis: diagData,
        })
      })
      .catch((err) => {
        console.warn('Failed to load active diagnosis:', err)
      })
      .finally(() => {
        if (isMounted) setDiagnosisLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [activeDatasetId])

  const selectStore = (id) => {
    if (!id) return
    setActiveDatasetId(String(id))
  }

  return (
    <StoreContext.Provider
      value={{
        datasets,
        activeDatasetId,
        selectStore,
        dataset,
        result,
        diagnosis,
        loading,
        diagnosisLoading,
        refreshStore: loadDatasets,
      }}
    >
      {children}
    </StoreContext.Provider>
  )
}

export function useStore() {
  const ctx = useContext(StoreContext)
  if (!ctx) {
    throw new Error('useStore must be used within a StoreProvider')
  }
  return ctx
}
