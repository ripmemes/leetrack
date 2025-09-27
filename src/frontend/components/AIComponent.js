import React , {useState ,useEffect} from 'react'

function AIComponent(){

    const [conversations , setConversations] = useState(null) 
    const [convoMsgs , setConvoMsgs ] = useState(null)
    const [convoId, setConvoId] = useState(-1) // useRef instead?
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
    const fetchMessages = async (convoId) => {
        console.log("test?")
        if (convoId ===-1) return ; // don't fetch 
        
        try {
            const response = await fetch(`http://localhost:5000/api/messages?conversation_id=${convoId}`,
                {method : 'GET',
                headers : {
                    'Content-Type' : 'application/json'
                }
                }
            )

            console.log("messages should've been fetched by now ?")

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
            const response = await fetch("http://localhost:5000/api/conversations", {
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

    const fetchConversation = async (convoId) => {
        try {
            const response = await fetch(`http://localhost:5000/api/conversations?conversation_id=${convoId}`, {
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
    const deleteConversation = async (convoId) => {
        try {
            const response = await fetch(`http://localhost:5000/api/deleteconvo?conversation_id=${convoId}`, {
             method : "DELETE"   
            } )

            if (!response.ok){
                const errorMsg = await response.json()['error']
                throw new Error("Network response was not ok, ", errorMsg)
            }

            const id = +convoMsgs[0].content // + : to convert string to int
            if (convoId==id){
                console.log("messages of current convo reset !")
                setConvoMsgs(null)
                renderChatBox()
            }
            setConversations(prev=>(prev.filter(msg=>msg.id!=id)))
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
    // TODO : get rid of unnecessary fetching, alternatively update local state in frontend
    // ----

    const sendMessage = async (e) =>{
        e.preventDefault()
        setSubmitting(true)
        setError(false)
        
        try{
            // TODO: user_id and problem_id are placeholders
            setConvoId(1)
            const response = await fetch("http://localhost:5000/api/ai" , {
                method : "POST",
                body: JSON.stringify({'message':message, 'user_id' : 1, 'problem_id': 1}),
                headers : { 
                    "Content-Type" : "application/json"
                }
            })
            if (!response.ok){
                throw new Error("Network response was not ok")
            }
           
            fetchMessages(convoId)
            fetchConversations()
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
            console.log("No conversations to render")
            return (<></>);
        }
        return (<ul className="flex flex-col bg-purple-500">
            {conversations.map(convo=>(
                <li key={convo.id} className="p-3 border-b hover:bg-purple-200">
                    <div className="flex items-center justify-between">
                        <button className="front-semibold" onClick={() => fetchMessages(convo.id) }>Conversation ID: {convo.id}</button>
                        <button className="absolute right-2 px-3 py-4" onClick={() => deleteConversation(convo.id)}>🗑️</button>
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
            console.log("No past conversation messages to render")
            return <></>
        }
        return (<div className="overflow-y-auto"><ul>
            {convoMsgs.map((msg,index)=>{
                
                if (msg.role === "assistant"){
                    // left 
                    return (
                        <li key={index} className="p-3 border-b bg-slate-400 hover:bg-gray-50"> 
                            <div  className="flex flex-col">
                                <span className="relative left-2">
                                    <p>{msg.content}</p>
                                </span>
                            </div>
                        </li>
                    )
                } else {
                    return (
                        <li key={msg.id} className="p-3 border-b bg-slate-600 hover:bg-gray-50"> 
                            <div  className="flex flex-col">
                                <span className="relative right-2">
                                    <p>{msg.content}</p>
                                </span>
                            </div>
                        </li>
                    )
                }
            })}        
        
        </ul></div>)
    }

   

    return (

        <div>
            <button onClick = {() => {
                setIsOpen(!isOpen)
                setMenuOpen(true)
                fetchConversations()
            }
            }>💬 Logo place holder 💬</button>
            {/* <button onClick = {() => setMenuOpen(!menuOpen)}> open conversation menu placeholder</button> */}
            {isOpen && <div className ="flex flex-row">
                {menuOpen ? renderConvoMenu() : (<></>)}
                {convoMsgs ? renderChatBox() : null}
                <form action="/" onSubmit ={sendMessage}>
                    <input type="text" disabled={submitting} value={message} onChange = {handleChange} />
                    <button className="bg-black hover:bg-slate-600" type ="submit" disabled={submitting || message.trim() == ""}>{submitting ? 'Submitting...' : 'Submit'}</button>
                </form>
                <div></div>
                
                {error && (<div className ="bg-red-600 relative right-1">Error : {error.message}</div>) }
            </div> 
            }
        </div>
    )
}

export default AIComponent