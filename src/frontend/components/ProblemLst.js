import React ,{ useEffect, useState, useRef, useCallback} from 'react'

function ProblemLst(){
    const [problems, setProblems] = useState([])
    // const [skip,setSkip] = useState(0)
    const skip = useRef(0)
    const [hasMore, setHasMore] = useState(true)

    const inFlight = useRef(false)

    const handleFetch = async () => {
        if (inFlight.current || !hasMore) return // To prevent duplicate calls
        inFlight.current = true 
        
        try {
            const response = await fetch(`http://localhost:5000/api/problems?skip=${skip.current}&limit=15`)
            skip.current += 15
            if (!response.ok){
                const errorData = await response.json()
                throw new Error(errorData.error || 'Network response was not ok')
            }


            const result = await response.json()
            console.log('Fetching is successful')
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
        handleFetch();
    }, []);

    // Adding Intersection Observer for lazy loading
    const loaderRef = useRef()

    useEffect( () => {
        if (!hasMore) return;
        const observer = new IntersectionObserver(
            entries => {
                if (entries[0].isIntersecting){
                    handleFetch();
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

    return (
        <div className="overflow-y-auto h-lvh">
            <ul>
                {problems.map(p =>(
                    <li key ={p.questionFrontendId}>
                        <div>{p.questionFrontendId}, {p.title} {p.difficulty}</div>
                    </li>
                ))}
            </ul>
            {hasMore && <div ref={loaderRef}> </div>}
        </div>
    )
} 

export default ProblemLst

