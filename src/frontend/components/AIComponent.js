import React , {useState ,useRef} from 'react'

function AIComponent({userId}){

    const [conversations , setConversations] = useState(null) 
    const [convoMsgs , setConvoMsgs ] = useState(null)
    
    const convoId = useRef(1) // this is the pointer to currently observed covnersation
    const convoEdge = useRef(1) // this is the pointer to the id of the next conversation
    const [message,setMessage] = useState("")

    // ------
    const [isOpen , setIsOpen] = useState(false) // Hide or show AI Diaglog box
    const [menuOpen, setMenuOpen] = useState(false) // Hide or Show conversations menu
    // ------
    const [submitting, setSubmitting] = useState(null)
    const [error , setError] = useState(false)

    // ------
    // fetch messages for a given conversation
    // ------
    const fetchMessages = async (conversationId) => {
        if (conversationId ===-1) return ; // don't fetch 
        
        try {
            const response = await fetch(`http://localhost:5000/api/messages?conversation_id=${conversationId}&user_id=${userId}`,
                {method : 'GET',
                headers : {
                    'Content-Type' : 'application/json'
                }
                }
            )

            console.log("fetchMessages: messages should've been fetched by now ?")

            if (!response.ok){
                const errorMsg = await response.json()['error']
                throw new Error("Network response was not ok, ", errorMsg)
            }

            const res = await response.json()
            setConvoMsgs(res)

        } catch (err){
            console.error("Error fetching messages for this conversation")
            setError(err)
            setConvoMsgs(null)
        }
    }


    // -----
    // fetch conversations 
    // -----

    const fetchConversations = async () => {
        try {
            const response = await fetch(`http://localhost:5000/api/conversations?user_id=${userId}`, {
                headers : {
                    "Content-Type" : "application/json"
                },
                method : "GET"
            })

            const result = await response.json()
            setConversations(result)
        }
        catch (err){
            console.error("Error fetching conversations")
            setConversations([])
        }
    }

    // -----
    // fetch data of a single conversation
    // TODO: unused for now
    // -----

    const fetchConversation = async (conversationId) => {
        try {
            const response = await fetch(`http://localhost:5000/api/conversations?conversation_id=${conversationId}&user_id=${userId}`, {
                headers : {
                    "Content-Type" : "application/json"
                },
                method : "GET"
            })

            const result = await response.json()
            // do something with it
        }
        catch (err){
            console.error("Error fetching conversations")
            setConversations([])
        }
    } 

    // ----
    // delete conversation
    // ----
    const deleteConversation = async (conversationId) => {
        try {
            const response = await fetch(`http://localhost:5000/api/deleteconvo?conversation_id=${conversationId}&user_id=${userId}`, {
             method : "DELETE"   
            } )

            if (!response.ok){
                const errorMsg = await response.json()['error']
                throw new Error("Network response was not ok, ", errorMsg)
            }

            // const id = +convoMsgs[0].content 
            console.log("deleteConversation : conversationId === " + conversationId)
            console.log("deleteConversation : convoId === " + convoId.current)
            if (conversationId===convoId.current){
                console.log("deleteConversation: messages of current convo reset !")
                setConvoMsgs(null)
                renderChatBox()
            }
            console.log("deleteConversation: setConversations to exclude deleted convo")
            setConversations(prev=>(prev.filter(msg=>msg.id!==conversationId)))
            renderConvoMenu()

        }
        catch (err){
            console.error("Error deleting conversation: ", err)
        }
    }

    // ----
    // update the message state according to field input
    // ----

    const handleChange= (e) => {
        setMessage(e.target.value)
    }

    // ----
    // send message to backend, to fetch reply through api request to openai
    // ----

    const sendMessage = async (e) =>{
        e.preventDefault()
        setSubmitting(true)
        setError(false)
        
        try{
            // TODO: problem_id is a placeholder
            console.log("sendMessage: convoId at this point : " + convoId.current)
            if (convoId.current == 0){
                convoId.current = 1 
            }
            const response = await fetch(`http://localhost:5000/api/ai?convoId=${convoId.current}` , {
                method : "POST",
                body: JSON.stringify({'message':message, 'user_id' : userId, 'problem_id': 1}),
                headers : { 
                    "Content-Type" : "application/json"
                }
            })
            if (!response.ok){
                throw new Error("Network response was not ok")
            }
            
            const result = await response.json()
            const qna = [{"role":"user","content":message},{"role":"assistant","content":result.reply}]
            setConvoMsgs(prev=>prev === null ? qna : [...prev,...qna])
            console.log("sendMessage: convoMsgs now: " + convoMsgs)
            setConversations(prev=>{
                if (prev === null){
                    return [{'id':convoId.current, 'created_at':new Date(), 'user_id' : 1,'problem_id' : 1}]
                }
                for (let i = 0 ; i < prev.length ; i++){
                    if (prev[i].id===convoId.current){
                        return prev;
                    }
                }
                // POSSIBLE ISSUE: date format might differ from that of python's datetime library
                return [...prev, {'id':convoId.current, 'created_at':new Date(), 'user_id' : 1,'problem_id' : 1}]
            })
            console.log("sendMessage: conversations now: " + conversations)
            return;
        } catch (err){
            console.error(err)
            setError(true)
        } finally{
            setSubmitting(false)
            setMessage("")
            renderChatBox()
            renderConvoMenu()
        }
    }
    
    // -----
    // Render Conversations Menu
    // -----

    const renderConvoMenu = () => {
        if (conversations == null){
            console.log("renderConvoMenu : No conversations to render")
            return (<></>);
        }
        return (<ul className="flex flex-col bg-purple-500">
            {conversations.map(convo=>(
                <li key={convo.id} className=" border-b ">
                    <div className="flex justify-between">
                        <button className="mr-auto front-semibold border rounded-ls max-w-xs hover:bg-purple-200" onClick={() => {
                            fetchMessages(convo.id)
                            convoId.current = convo.id
                            } }>Conversation ID: {convo.id}</button>
                        <button className="ml-auto px-3 py-4 border rounded-ls max-w-xs hover:bg-purple-200" onClick={() => {
                            deleteConversation(convo.id)
                            if (convo.id === convoEdge.current){
                                convoEdge.current = convoEdge.current === 1 ? 1: convoEdge.current-1
                            } 
                            // convoId.current = convo.id -1 
                            }}>🗑️</button>
                    </div>
                </li>
                )) 
            }
        </ul>)
    }

    // -----
    // Render Chat Box
    // -----

    const renderChatBox = () => {
        if (convoMsgs == null){
            console.log("renderChatBox: No past conversation messages to render")
            return <></>
        }
        return ( 
        <div className="overflow-y-auto"><ul>
            {convoMsgs.map((msg,index)=>(
                <li key={index} className="hover:bg-gray-50 flex mb-2"> 
                {msg.role === "assistant" ? (
                    <div  className="bg-slate-400 px-3 py-4 rounded-lg max-w-xs">
                        <span className="relative left-2">
                            <p>{msg.content}</p>
                        </span>
                    </div>
                ) : (<div  className="ml-auto bg-slate-600 px-3 py-2 rounded-lg max-w-xs right-4">
                        <span className="relative right-2">
                            <p>{msg.content}</p>
                        </span>
                    </div>  
                ) }
                </li>
              
                 
            ))}
            </ul></div>
        )

    }

   

    return (

        <div>
            <div className="flex justify-center items-center">
            <button onClick = {() => {
                setIsOpen(!isOpen)
                setMenuOpen(true)
                fetchConversations()
            }
            }>💬 Logo place holder 💬</button></div>
            {/* <button onClick = {() => setMenuOpen(!menuOpen)}> open conversation menu placeholder</button> */}
            {isOpen && <div className="border rounded-md"><div className ="flex flex-row">
                {menuOpen && renderConvoMenu()}
                {convoMsgs && renderChatBox()}
                </div><div className="flex flex-row items-center justify-center ">
                    <form action="/" onSubmit ={sendMessage}>
                        <input type="text" disabled={submitting} value={message} onChange = {handleChange} />
                        <button className="bg-black hover:bg-slate-600" type ="submit" disabled={submitting || message.trim() === ""}>{submitting ? 'Submitting...' : 'Submit'}</button>
                    </form>
                    <button className ="border-spacing-2 border shadow-md py-4 mx-4 font-bold" onClick ={()=> {
                        if (convoMsgs !== null){
                            convoEdge.current += 1
                            convoId.current = convoEdge.current
                            setConvoMsgs(null)
                        }
                    }}>Create new conversation!!!</button>
                </div>
                
                
                {error && (<div className ="bg-red-600 relative right-1">Error : {error.message}</div>) }
                </div>
            }
        </div>
    )
}

export default AIComponent