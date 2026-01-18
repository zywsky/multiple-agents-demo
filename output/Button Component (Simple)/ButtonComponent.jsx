```jsx
import React, { useState, useEffect } from'react';
import Button from '@mui/material/Button';

const ButtonComponent = ({ text, href, element }) => {
    const [isClicked, setIsClicked] = useState(false);

    useEffect(() => {
        const button = document.querySelectorAll('.example-button');
        button.forEach((btn) => {
            if (btn.hasAttribute('disabled')) {
                btn.classList.add('disabled-class');
            }
        });
    }, []);

    const handleClick = () => {
        setIsClicked(true);
        // 模拟添加和移除特定CSS类的动画效果
        const button = document.querySelector('.example-button');
        button.classList.add('clicked-class');
        setTimeout(() => {
            button.classList.remove('clicked-class');
        }, 500);
    };

    return (
        <Button
            href={href}
            component={element === 'button'? 'button' : 'a'}
            variant="contained"
            onClick={handleClick}
            className="example-button"
        >
            {text}
        </Button>
    );
};

ButtonComponent.propTypes = {
    text: PropTypes.string.isRequired,
    href: PropTypes.string,
    element: PropTypes.oneOf(['button', 'a']).isRequired
};

export default ButtonComponent;
```