import React, {useState} from 'react'

export const Form = ({formType,fieldArr,backendURL}) => {
    // here I need to create the default field dictionary 
    const defaultDictState = {}

    for (let i = 0 ; i < fieldArr.length ; i++){
        defaultDictState[fieldArr[i].toLowerCase()] = '';
    }

    const [formData , setFormData] = useState(defaultDictState);
    const [message, setMessage] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleChange = (e) => {
        const {name , value} = e.target;
        setFormData( { ...formData , [name] : value});
    }


    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setMessage(null);
        

        try {
            if (formData['confirm password'] && formData['confirm password'] !== formData['password'] ){
                throw new Error("The password in 'Confirm Password' field doesn't match the one in 'Password' field")
            }
            const response = await fetch(`http://localhost:5000/${backendURL}`, {
                method : 'POST',
                headers : {
                    'Content-Type' : 'application/json'
                },
                body : JSON.stringify(formData),
            });

            
            
            if (response.status == 404){
                throw new Error("Network response was not ok")
            }
            if (!response.ok){
                throw new Error('Network response was not ok')
            } 
            if (response.redirected){
                window.location.href = response.url 
                return; 
            }

            const result = await response.json();
            // Parse the JSON from backend

            
            setMessage({type: 'success', text: result.message});
            setFormData(defaultDictState);
        } catch (error) {
            console.error('Submission Error:' , error);
            setMessage({type : 'error', text: `Failed to submit form: ${error.message}`});
        } finally {
            setIsSubmitting(false);
        }
    }


    return ( <>
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
            
            <div className="bg-white shadow-lg rounded-xl p-8 w-full max-w-md">
                <h1 className ="text-3xl font-bold text-center text-gray-800 mb-10"> { formType } Form</h1>
                <p className ="mb-5 text-xl font-bold text-gray-900">Please fill out the following fields :</p>
                <form action ={`/${backendURL}`} method="POST" onSubmit={handleSubmit} className="space-y-4">
                    {fieldArr.map((field) => (
                        <div key = {field} className="flex flex-col">
                            <label htmlFor= {field} className ="text-gray-700 capitalize mb-1 font-medium">
                                {field.charAt(0).toUpperCase() + field.slice(1)}
                            </label>
                            <input type={field.toLowerCase().includes('password') ? 'password' : 'text'}
                                    id = {field}
                                    name = {field.toLowerCase()}
                                    value = {formData[field.toLowerCase()]}
                                    onChange = {handleChange}
                                    disabled = {isSubmitting}
                                    required
                                    className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                            />
                        </div>
                    ))}
                <div className ="flex justify-center"><button type="submit" disabled={isSubmitting} 
                className = "mx-auto bg-blue-600 w-full text-white font-semibold py-3 px-4 rounded-lg shadow-md hover:bg-blue-700 transition-colors duration-300 disabled:bg-blue-300 ">
                    {isSubmitting ? 'Submitting...' : 'Submit'}
                </button></div>
                </form>
                {message && (
                <div className ={`mt-4 p-3 rounded-lg text-center font-medium ${message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-200 text-red-700'}`}>
                    {message.text}
                </div>  
            )}
            
            </div>
        </div>
        
    </>)
};

export const LoginForm = () => {
  return <Form formType="Login" fieldArr={["Username/E-Mail","Password"]} backendURL="login" />  
};
export const RegisterForm = () => {
    return <Form formType="Register" fieldArr={["E-Mail","Password","Confirm Password","Username"]} backendURL="register" />  
  };