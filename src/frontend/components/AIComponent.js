import React, { useCallback, useEffect, useRef, useState } from 'react'

function AIComponent({ userId }) {
    const [conversations, setConversations] = useState([])
    const [convoMsgs, setConvoMsgs] = useState(null)
    const [message, setMessage] = useState('')
    const [isOpen, setIsOpen] = useState(false) // Hide or show AI Dialog box
    const [isMinimized, setIsMinimized] = useState(false)
    const [menuOpen, setMenuOpen] = useState(true) // Hide or show conversations menu
    const [submitting, setSubmitting] = useState(false)
    const [error, setError] = useState(null) // changed to null

    const convoId = useRef(1) // this is the pointer to the currently observed conversation
    const convoEdge = useRef(1) // this is the pointer to the id of the next conversation

    const fetchConversations = useCallback(async () => {
        try {
            const response = await fetch(`http://localhost:5000/api/conversations?user_id=${userId}`, {
                headers: {
                    'Content-Type': 'application/json'
                },
                method: 'GET'
            })

            if (!response.ok) {
                throw new Error('Could not fetch conversations')
            }

            const result = await response.json()
            setConversations(result || [])
        } catch (err) {
            console.error('Error fetching conversations', err)
            setConversations([])
        }
    }, [userId])

    useEffect(() => {
        if (isOpen && userId) {
            fetchConversations()
        }
    }, [isOpen, userId, fetchConversations])

    const fetchMessages = async (conversationId) => {
        if (conversationId === -1) return

        try {
            const response = await fetch(
                `http://localhost:5000/api/messages?conversation_id=${conversationId}&user_id=${userId}`,
                {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
            )

            if (!response.ok) {
                const errorMsg = await response.json()['error']
                throw new Error(errorMsg || 'Network response was not ok')
            }

            const res = await response.json()
            setConvoMsgs(res)
        } catch (err) {
            console.error('Error fetching messages for this conversation', err)
            setError(err)
            setConvoMsgs(null)
        }
    }

    const deleteConversation = async (conversationId) => {
        try {
            const response = await fetch(
                `http://localhost:5000/api/deleteconvo?conversation_id=${conversationId}&user_id=${userId}`,
                {
                    method: 'DELETE'
                }
            )

            if (!response.ok) {
                const errorMsg = await response.json()['error']
                throw new Error(errorMsg || 'Could not delete conversation')
            }

            if (conversationId === convoId.current) {
                setConvoMsgs(null)
            }

            setConversations((prev) => prev.filter((msg) => msg.id !== conversationId))
        } catch (err) {
            console.error('Error deleting conversation: ', err)
        }
    }

    const handleChange = (e) => {
        setMessage(e.target.value)
    }

    const sendMessage = async (e) => {
        e.preventDefault()
        setSubmitting(true)
        setError(null)

        try {
            if (convoId.current === 0) {
                convoId.current = 1
            }

            const response = await fetch(`http://localhost:5000/api/ai?convoId=${convoId.current}`, {
                method: 'POST',
                body: JSON.stringify({ message, user_id: userId, problem_id: 1 }),
                headers: {
                    'Content-Type': 'application/json'
                }
            })

            if (!response.ok) {
                throw new Error('Network response was not ok')
            }

            const result = await response.json()
            const qna = [
                { role: 'user', content: message },
                { role: 'assistant', content: result.reply }
            ]

            setConvoMsgs((prev) => (prev === null ? qna : [...prev, ...qna]))
            setConversations((prev) => {
                if (prev.some((item) => item.id === convoId.current)) {
                    return prev
                }

                return [
                    ...prev,
                    {
                        id: convoId.current,
                        created_at: new Date(),
                        user_id: userId,
                        problem_id: 1
                    }
                ]
            })
        } catch (err) {
            console.error(err)
            setError(err)
        } finally {
            setSubmitting(false)
            setMessage('')
        }
    }

    const renderConvoMenu = () => (
        <div className="w-40 border-r border-slate-200 bg-slate-50 p-2">
            <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Chats</p>
            <ul className="space-y-2">
                {conversations.map((convo) => (
                    <li key={convo.id} className="rounded-lg border border-slate-200 bg-white">
                        <div className="flex items-center justify-between gap-2 p-2">
                            <button
                                className="flex-1 text-left text-xs font-medium text-slate-700 hover:text-orange-600"
                                onClick={() => {
                                    fetchMessages(convo.id)
                                    convoId.current = convo.id
                                }}
                            >
                                Chat #{convo.id}
                            </button>
                            <button
                                className="text-slate-400 hover:text-red-500"
                                onClick={() => deleteConversation(convo.id)}
                                aria-label="Delete conversation"
                            >
                                🗑️
                            </button>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    )

    const renderChatBox = () => {
        if (!convoMsgs || convoMsgs.length === 0) {
            return (
                <div className="flex h-full items-center justify-center text-sm text-slate-500">
                    Start a new conversation
                </div>
            )
        }

        return (
            <div className="h-full overflow-y-auto p-3">
                <ul className="space-y-2">
                    {convoMsgs.map((msg, index) => (
                        <li key={`${msg.role}-${index}`} className={`flex ${msg.role === 'assistant' ? 'justify-start' : 'justify-end'}`}>
                            <div
                                className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm ${
                                    msg.role === 'assistant'
                                        ? 'bg-slate-200 text-slate-800'
                                        : 'bg-orange-500 text-white'
                                }`}
                            >
                                {msg.content}
                            </div>
                        </li>
                    ))}
                </ul>
            </div>
        )
    }

    return (
        <div className="relative">
            {!isOpen ? (
                <button
                    onClick={() => {
                        setIsOpen(true)
                        setIsMinimized(false)
                        setMenuOpen(true)
                        fetchConversations()
                    }}
                    className="flex items-center gap-2 rounded-full border border-orange-200 bg-white px-4 py-3 text-sm font-semibold text-slate-800 shadow-xl transition hover:-translate-y-0.5 hover:shadow-2xl"
                >
                    <span className="text-lg">💬</span>
                    Chat with AI Assistant
                </button>
            ) : (
                <div className="w-[360px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
                    <div className="flex items-center justify-between bg-slate-900 px-4 py-3 text-white">
                        <div>
                            <p className="text-sm font-semibold">AI Assistant</p>
                            <p className="text-[10px] uppercase tracking-[0.2em] text-slate-300">LeetTrack</p>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                className="rounded-md border border-slate-600 px-2 py-1 text-[10px] font-medium text-slate-200 hover:bg-slate-700"
                                onClick={() => setIsMinimized((prev) => !prev)}
                            >
                                {isMinimized ? 'Open' : 'Minimize'}
                            </button>
                            <button
                                className="rounded-md border border-slate-600 px-2 py-1 text-[10px] font-medium text-slate-200 hover:bg-slate-700"
                                onClick={() => setIsOpen(false)}
                            >
                                Hide
                            </button>
                        </div>
                    </div>

                    {!isMinimized && (
                        <>
                            <div className="flex h-[420px]">
                                {menuOpen && renderConvoMenu()}
                                <div className="flex-1 bg-slate-50">{renderChatBox()}</div>
                            </div>

                            <div className="border-t border-slate-200 bg-white p-3">
                                <div className="mb-2 flex items-center justify-between gap-2">
                                    <button
                                        className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500 hover:text-orange-600"
                                        onClick={() => setMenuOpen((prev) => !prev)}
                                    >
                                        {menuOpen ? 'Hide chats' : 'Show chats'}
                                    </button>
                                    <button
                                        className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500 hover:text-orange-600"
                                        onClick={() => {
                                            convoEdge.current += 1
                                            convoId.current = convoEdge.current
                                            setConvoMsgs(null)
                                        }}
                                    >
                                        New chat
                                    </button>
                                </div>

                                <form className="flex gap-2" onSubmit={sendMessage}>
                                    <input
                                        type="text"
                                        value={message}
                                        onChange={handleChange}
                                        disabled={submitting}
                                        className="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none ring-0 placeholder:text-slate-400 focus:border-orange-400"
                                        placeholder="Ask the AI..."
                                    />
                                    <button
                                        type="submit"
                                        disabled={submitting || message.trim() === ''}
                                        className="rounded-lg bg-orange-500 px-3 py-2 text-sm font-semibold text-white transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:bg-slate-300"
                                    >
                                        {submitting ? '...' : 'Send'}
                                    </button>
                                </form>
                            </div>
                        </>
                    )}

                    {error && (
                        <div className="border-t border-red-200 bg-red-50 px-3 py-2 text-xs text-red-600">
                            Error: {error.message}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default AIComponent