// React Component Code
import React, { useEffect, useRef } from'react';

// Assume BDLButton is a BDL component for the button
import BDLButton from '@company/bdl-components/BDLButton';
import styles from './Button.module.css';

// Props interface based on AEM dialog configuration
interface ButtonProps {
    text: string;
    href: string;
    element: 'button' | 'a';
}

// 使用useRef来获取BDLButton的引用，以便进行类型检查
const bdlButtonRef = useRef<BDLButton>(null);

const Button: React.FC<ButtonProps> = ({ text, href, element }) => {
    useEffect(() => {
        const initButton = () => {
            const buttons = bdlButtonRef.current?.getElementsByClassName('example-button');
            if (buttons) {
                Array.from(buttons).forEach((button) => {
                    if (button.disabled) {
                        button.classList.add(styles['example-button--disabled']);
                    }
                    button.addEventListener('click', () => {
                        button.classList.add(styles['example-button--clicked']);
                        setTimeout(() => {
                            button.classList.remove(styles['example-button--clicked']);
                        }, 300);
                    });
                });
            }
        };
        const injectButtonStyles = () => {
            const style = document.createElement('style');
            style.textContent = `
              .${styles['example-button--clicked']} {
                    transform: scale(0.95);
                    transition: transform 0.1s ease;
                }
              .${styles['example-button--disabled']} {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
            `;
            document.head.appendChild(style);
        };
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                initButton();
                injectButtonStyles();
            });
        } else {
            initButton();
            injectButtonStyles();
        }
        return () => {
            // Cleanup any event listeners or DOM manipulations if needed
        };
    }, []);

    useEffect(() => {
        if (bdlButtonRef.current) {
            // 在这里可以进行BDLButton组件的类型检查
            console.log('BDLButton instance:', bdlButtonRef.current);
        }
    }, [bdlButtonRef.current]);

    return (
        <BDLButton
            ref={bdlButtonRef}
            text={text}
            href={href}
            element={element}
            sx={{ color: 'primary', '@media (max-width: 600px)': { fontSize: '14px' } }}
            className={styles['example-button']}
        />
    );
};

export default Button;