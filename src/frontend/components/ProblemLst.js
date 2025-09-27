import React ,{ useEffect, useState, useRef} from 'react'

function ProblemLst(){
    const languageSlugs = 
    [
        "cpp",
        "java",
        "python",
        "python3",
        "c",
        "csharp",
        "javascript",
        "typescript",
        "php",
        "swift",
        "kotlin",
        "dart",
        "go",
        "ruby",
        "scala",
        "rust",
        "racket",
        "erlang",
        "elixir"
      ]
    
      const topicSlugs = 
      [
        "array",
        "string",
        "hash-table",
        "dynamic-programming",
        "math",
        "sorting",
        "greedy",
        "depth-first-search",
        "breadth-first-search",
        "tree",
        "binary-tree",
        "binary-search",
        "graph",
        "design",
        "stack",
        "union-find",
        "heap-priority-queue",
        "matrix",
        "simulation",
        "backtracking",
        "bit-manipulation",
        "sliding-window",
        "two-pointers",
        "linked-list",
        "queue",
        "recursion",
        "divide-and-conquer",
        "trie",
        "ordered-set",
        "monotonic-stack",
        "number-theory",
        "geometry",
        "topological-sort",
        "segment-tree",
        "binary-indexed-tree",
        "line-sweep",
        "rolling-hash",
        "brainteaser",
        "game-theory",
        "combinatorics",
        "data-stream"
      ]
    const [problems, setProblems] = useState([])
    // const [skip,setSkip] = useState(0)
    const skip = useRef(0)
    const [hasMore, setHasMore] = useState(true)
    const [showFilters, setShowFilters] = useState(false)
    const inFlight = useRef(false)

    // -----
    // filters useState variable
    // -----

    const [filters , setFilters] = useState({difficulties : [], languages : [] , topics : []})

    const handleFetch = async (currentFilters=filters) => {
        if (inFlight.current || !hasMore){ 
            return // To prevent duplicate calls
        }
        inFlight.current = true 
        
        try {
            let query = `http://localhost:5000/api/problems?skip=${skip.current}&limit=15`
            currentFilters.difficulties.forEach(d => {
                query +=`&difficulties=${d}`
            })
            currentFilters.topics.forEach(t=>{
                query+=`&topics=${t}`
            })
            currentFilters.languages.forEach(l=>{
                query+=`&languages=${l}`
            })
            const response = await fetch(query)
            skip.current += 30
            if (!response.ok){
                const errorData = await response.json()
                throw new Error(errorData.error || 'Network response was not ok')
            }


            const result = await response.json()
            const newProblems = result['questions'] ?? []
            setHasMore(result.hasMore)
            setProblems(prev => [...prev, ...newProblems])

        }
        
        catch(err){
             console.error(err)
        }
        finally{
            inFlight.current = false
        }

    }

    
      

    useEffect(() => {
        handleFetch(filters);
    }, []);

    // Adding Intersection Observer for lazy loading
    const loaderRef = useRef()

    useEffect( () => {
        if (!hasMore) return;
        const observer = new IntersectionObserver(
            entries => {
                if (entries[0].isIntersecting){
                    handleFetch(filters);
                }
            },
            {threshold:0.5}
        )
        if (loaderRef.current){
            observer.observe(loaderRef.current)
        }
        return () => {
            if (loaderRef.current){
                observer.unobserve(loaderRef.current);
            }
        }
    }, [hasMore, handleFetch]);

    const handleDifficultyChange =(value) => {
        setFilters(prev=>{
            const difficulties = prev.difficulties.includes(value) ? prev.difficulties.filter(d=> d!==value)
            : [...prev.difficulties, value]
            return {...prev, difficulties}
     });
    }

    const handleLanguageChange = (e) => {
        const selectedOptions = Array.from(e.target.selectedOptions , option => option.value)
        setFilters(prev => ({...prev, languages:selectedOptions }))
    }

    const handleTopicChange = (e) => {
        const selectedOptions = Array.from(e.target.selectedOptions , option => option.value)
        setFilters(prev => ({...prev, topics:selectedOptions}))
    }

    const applyFilters = () => {
        skip.current = 0 
        setProblems([])
        setHasMore(true) 
        handleFetch(filters)
    }

    useEffect(()=> {
        
        handleFetch(filters)

    }, [])

    const filterBar = () => {
        return (
            <div className="mx-3 flex flex-col border bg-slate-400 hover:bg-slate-100">
                <div className="mx-3 flex flex-row">
                {["EASY","MEDIUM","HARD"].map(diff =>(
                    <label key={diff} className="mx-2 flex items-center gap-1">
                        {diff}
                        <input 
                         type="checkbox"
                         value={diff}
                         checked={filters.difficulties.includes(diff)}
                         onChange={()=> handleDifficultyChange(diff)}
                        >
                        </input>
                    
                    </label>
                ) )}
                </div>
                <select
                 multiple
                 value={filters.languages}
                 onChange = {handleLanguageChange}
                 className="border rounded p-1"
                 >
                    {languageSlugs.map(lang => (
                        <option key ={lang} value ={lang}>
                            {lang}
                        </option>
                    ))}
                 </select>

                <select
                 multiple
                 value ={filters.topics}
                 onChange = {handleTopicChange}
                 className = "border rounded p-1"
                 >
                    {topicSlugs.map(top => (
                        <option key ={top} value = {top}>
                            {top}
                        </option>
                    ))}
                 </select>

                <button className="ml-4 px-3 py-1 bg-blue-500 text-white rounded" onClick={applyFilters}>
                    Apply
                </button>
            </div>
        )
    }
    return (
        <div className="overflow-y-auto h-lvh">
            <button className="my-3 ml-4 px-3 py-1 bg-blue-500 hover:bg-blue-300 text-white rounded" onClick={() => setShowFilters(!showFilters)}>Filters:</button>
            <div className="">
            {showFilters && filterBar()}
            </div>
            
            <ul>
                {problems.map((p,index) =>(
                    <li key ={index} className="p-3 border-b hover:bg-gray-50">
                        <div className="flex items-center justify-between">
                            <span className="font-semibold">{index+1}, {p.title} </span>
                            <span className={`px-2 py-1 rounded-md border text-sm font-medium
                            ${p.difficulty.toLowerCase() === "easy" ? "border-green-500 text-green-600" : ""}
                            ${p.difficulty.toLowerCase() === "medium" ? " border-yellow-500 text-yellow-600" : ""}
                            ${p.difficulty.toLowerCase() === "hard" ? "border-red-500 text-red-600" : ""}`}>
                            {p.difficulty}
                            </span>
                        </div>
                    </li>
                ))}
            </ul>
            {hasMore && <div ref={loaderRef}> </div>}
        </div>
    )
} 

export default ProblemLst

